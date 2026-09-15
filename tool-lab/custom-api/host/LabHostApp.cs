#nullable enable

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Threading;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace Amanda.ToolLab.Host;

/// <summary>
/// Autonomous host for the P02-T16 custom-API fallback proof.
///
/// The host is a standalone Revit add-in that depends on neither Horizun nor
/// RevitCortex. It reads a job file next to its own assembly, drives one
/// disposable document through the independently compiled
/// <see cref="Amanda.ToolLab.CustomApi.CreateLabWall"/> external command, and
/// writes a machine-readable result before asking Revit to exit.
/// </summary>
public sealed class LabHostApp : IExternalApplication
{
    private ExternalEvent? externalEvent;

    public Result OnStartup(UIControlledApplication application)
    {
        try
        {
            LabHostFiles.Journal("OnStartup: entering");
            var handler = new LabHostHandler();
            externalEvent = ExternalEvent.Create(handler);
            externalEvent.Raise();
            LabHostFiles.Journal("OnStartup: external event raised");
            return Result.Succeeded;
        }
        catch (Exception exception)
        {
            LabHostFiles.Journal("OnStartup: failed: " + exception);
            return Result.Failed;
        }
    }

    public Result OnShutdown(UIControlledApplication application)
    {
        LabHostFiles.Journal("OnShutdown");
        return Result.Succeeded;
    }
}

internal static class LabHostFiles
{
    public static string BaseDirectory =>
        Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location) ?? AppContext.BaseDirectory;

    public static string JobPath
    {
        get
        {
            var configuredPath = Environment.GetEnvironmentVariable("AMANDA_LAB_HOST_JOB");
            return string.IsNullOrWhiteSpace(configuredPath)
                ? Path.Combine(BaseDirectory, "host-job.json")
                : configuredPath;
        }
    }

    public static string DefaultResultPath => Path.Combine(BaseDirectory, "host-result.json");

    public static string StatusPath => Path.Combine(BaseDirectory, "host-status.log");

    public static void Journal(string message)
    {
        try
        {
            File.AppendAllText(
                StatusPath,
                DateTime.UtcNow.ToString("o") + " " + message + Environment.NewLine);
        }
        catch
        {
            // Journaling must never break the run.
        }
    }
}

internal sealed class JobSpec
{
    public JobSpec(string mode, string workRvt, string standbyRvt, string resultPath, string statusPath, long expectElementIdValue, int expectedPid, string envToken)
    {
        Mode = mode;
        WorkRvt = workRvt;
        StandbyRvt = standbyRvt;
        ResultPath = resultPath;
        StatusPath = statusPath;
        ExpectElementIdValue = expectElementIdValue;
        ExpectedPid = expectedPid;
        EnvToken = envToken;
    }

    public string Mode { get; }

    public string WorkRvt { get; }

    public string StandbyRvt { get; }

    public string ResultPath { get; }

    public string StatusPath { get; }

    public long ExpectElementIdValue { get; }

    public int ExpectedPid { get; }

    public string EnvToken { get; }
}

internal sealed class LabHostHandler : IExternalEventHandler
{
    private static int runCount;
    private static string lastStandDownReason = string.Empty;

    public void Execute(UIApplication app)
    {
        if (Interlocked.Increment(ref runCount) > 1)
        {
            return;
        }

        new LabHostRun(app).Execute();
    }

    public static string LastStandDownReason => lastStandDownReason;

    public string GetName() => "Amanda P02-T16 custom API lab host";
}

/// <summary>
/// Decides whether this Revit process is allowed to run the lab job.
///
/// The guard exists because the lab add-in is installed in the shared per-user
/// add-ins folder, so any Revit instance on this machine can load it. Only the
/// process named by the job may act; anything else stands down untouched.
/// </summary>
internal static class OwnershipGuard
{
    public static string? Check(UIApplication app, JobSpec job)
    {
        if (job.ExpectedPid <= 0)
        {
            return "job does not name an owning pid; refusing to act";
        }

        if (job.ExpectedPid != Environment.ProcessId)
        {
            return $"job targets pid {job.ExpectedPid}, this process is {Environment.ProcessId}";
        }

        // Launch token: only a process started by the lab runner inherits the
        // token in its environment. This proves ownership even if a pid happens
        // to be reused, and it is the guard that keeps any other Revit session
        // on this machine completely inert.
        var tokenInJob = job.EnvToken;
        var tokenInProcess = Environment.GetEnvironmentVariable("AMANDA_LAB_HOST_TOKEN");

        if (string.IsNullOrEmpty(tokenInJob))
        {
            return "job does not carry a launch token; refusing to act";
        }

        if (!string.Equals(tokenInJob, tokenInProcess, StringComparison.Ordinal))
        {
            return "launch token does not match this process environment";
        }

        var activePath = app.ActiveUIDocument?.Document?.PathName;
        if (string.IsNullOrWhiteSpace(activePath))
        {
            return "active document path is unavailable; refusing to act";
        }

        if (string.IsNullOrWhiteSpace(job.WorkRvt))
        {
            return "job does not name a disposable work file; refusing to act";
        }

        if (!string.Equals(activePath, job.WorkRvt, StringComparison.OrdinalIgnoreCase))
        {
            return $"active document '{activePath}' is not the disposable work file";
        }

        return null;
    }
}

internal sealed class LabHostRun
{
    private const string KnownLevelName = "Level 1";
    private const double ExpectedLengthMetres = 5.0;
    private const double ExpectedHeightMetres = 3.0;
    private const double ToleranceMetres = 0.01;

    private readonly UIApplication app;
    private readonly Dictionary<string, object?> result = new();
    private readonly List<Dictionary<string, object?>> steps = new();
    private string resultPath = LabHostFiles.DefaultResultPath;

    public LabHostRun(UIApplication app)
    {
        this.app = app;
    }

    public void Execute()
    {
        var total = Stopwatch.StartNew();
        var standDown = false;
        try
        {
            LabHostFiles.Journal("handler: Execute entered");
            var job = LoadJob();
            resultPath = job.ResultPath;

            var standDownReason = OwnershipGuard.Check(app, job);
            if (standDownReason != null)
            {
                LabHostFiles.Journal("guard: standing down: " + standDownReason);
                steps.Add(new Dictionary<string, object?>
                {
                    ["name"] = "ownership-guard",
                    ["status"] = "STAND_DOWN",
                    ["duration_ms"] = 0L,
                    ["detail"] = standDownReason,
                });
                result["outcome"] = "STAND_DOWN";
                result["steps"] = steps;
                standDown = true;
                return;
            }

            result["job"] = new Dictionary<string, object?>
            {
                ["mode"] = job.Mode,
                ["work_rvt"] = job.WorkRvt,
                ["expect_element_id_value"] = job.ExpectElementIdValue,
            };

            try
            {
                RunJob(job);
                result["outcome"] = "PASS";
            }
            catch (Exception exception)
            {
                result["outcome"] = "FAIL";
                result["failure"] = exception.ToString();
                LabHostFiles.Journal("handler: job failed: " + exception.Message);
            }
        }
        catch (Exception exception)
        {
            result["outcome"] = "FAIL";
            result["failure"] = "bootstrap failed: " + exception;
            LabHostFiles.Journal("handler: bootstrap failed: " + exception);
        }
        finally
        {
            result["total_ms"] = total.ElapsedMilliseconds;
            result["steps"] = steps;
            result["recorded_utc"] = DateTime.UtcNow.ToString("o");
            result["host_assembly"] = Assembly.GetExecutingAssembly().Location;

            // A stand-down must be invisible: no result file for the runner to
            // mistake for a completed job, and no exit request for a Revit
            // session that this add-in does not own.
            if (standDown)
            {
                LabHostFiles.Journal("handler: standing down; no result file and no Revit state change");
            }
            else
            {
                WriteResult();
            }
        }
    }

    private void RunJob(JobSpec job)
    {
        if (string.IsNullOrWhiteSpace(job.WorkRvt))
        {
            throw new InvalidOperationException("job.work_rvt is required");
        }

        if (!File.Exists(job.WorkRvt))
        {
            throw new FileNotFoundException("job.work_rvt does not exist", job.WorkRvt);
        }

        if (string.Equals(job.Mode, "verify", StringComparison.OrdinalIgnoreCase))
        {
            RunVerify(job);
            return;
        }

        RunCreate(job);
    }

    private void RunCreate(JobSpec job)
    {
        Document document = null!;
        ElementId wallId = ElementId.InvalidElementId;
        long wallIdValue = 0L;

        if (string.IsNullOrWhiteSpace(job.StandbyRvt))
        {
            throw new InvalidOperationException("job.standby_rvt is required to close the active work document safely");
        }

        if (!File.Exists(job.StandbyRvt))
        {
            throw new FileNotFoundException("job.standby_rvt does not exist", job.StandbyRvt);
        }

        if (string.Equals(job.StandbyRvt, job.WorkRvt, StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException("job.standby_rvt must be a different disposable file");
        }

        Step("open-work-document", () =>
        {
            var uidocument = app.OpenAndActivateDocument(job.WorkRvt);
            document = uidocument.Document;
            result["document_title"] = document.Title;
            result["is_family_document"] = document.IsFamilyDocument;
            if (document.IsFamilyDocument)
            {
                throw new InvalidOperationException("a project document is required");
            }
        });

        Step("prepare-fixture-level", () => PrepareKnownLevel(document));

        var wallsBefore = new HashSet<long>();
        Step("snapshot-walls-before", () =>
        {
            wallsBefore = CollectWallIds(document);
            result["wall_count_before"] = wallsBefore.Count;
        });

        Step("invoke-external-command", () => wallId = InvokeExternalCommand());

        Step("locate-new-wall", () =>
        {
            var wallsAfter = CollectWallIds(document);
            var created = wallsAfter.Except(wallsBefore).ToArray();
            result["wall_count_after"] = wallsAfter.Count;
            if (created.Length != 1)
            {
                throw new InvalidOperationException(
                    $"expected exactly one new wall, observed {created.Length}");
            }

            wallId = new ElementId(created[0]);
            wallIdValue = wallId.Value;
            result["command_reported_element_id_value"] = reportedElementIdValue;
            result["element_id_value"] = wallIdValue;
            result["element_id_matches_command_report"] = reportedElementIdValue == wallIdValue;
        });

        Step("verify-geometry-in-session", () => VerifyWall(document, wallId, "in_session"));

        Step("save-document", () =>
        {
            var watch = Stopwatch.StartNew();
            document.Save();
            result["save_ms"] = watch.ElapsedMilliseconds;
        });

        Step("activate-standby-document", () =>
        {
            var uidocument = app.OpenAndActivateDocument(job.StandbyRvt);
            result["standby_document_title"] = uidocument.Document.Title;
        });

        Step("close-document", () =>
        {
            var closedDocumentTitle = document.Title;
            document.Close(false);
            result["closed_document_title"] = closedDocumentTitle;
        });

        Step("reopen-document", () =>
        {
            var uidocument = app.OpenAndActivateDocument(job.WorkRvt);
            document = uidocument.Document;
        });

        Step("verify-persistence-after-reopen", () =>
        {
            result["reopened_document_title"] = document.Title;
            result["wall_count_after_reopen"] = CollectWallIds(document).Count;
            VerifyWall(document, new ElementId(wallIdValue), "after_reopen");
        });

        Step("activate-standby-document-final", () =>
        {
            app.OpenAndActivateDocument(job.StandbyRvt);
        });

        Step("close-document-final", () =>
        {
            // Only the disposable work document is touched. Any other document
            // that Revit restored belongs to the owner and is left untouched.
            var workDocument = app.Application.Documents
                .Cast<Document>()
                .FirstOrDefault(candidate =>
                    !candidate.IsLinked &&
                    string.Equals(
                        candidate.PathName,
                        job.WorkRvt,
                        StringComparison.OrdinalIgnoreCase));

            if (workDocument == null)
            {
                result["close_document_final"] = "already closed";
                return;
            }

            workDocument.Close(false);
            result["close_document_final"] = "closed " + job.WorkRvt;
        });
    }

    private void RunVerify(JobSpec job)
    {
        Document document = null!;
        Step("open-work-document", () =>
        {
            var uidocument = app.OpenAndActivateDocument(job.WorkRvt);
            document = uidocument.Document;
            result["document_title"] = document.Title;
            result["wall_count_after_reopen"] = CollectWallIds(document).Count;
        });

        Step("verify-persistence-external-run", () =>
        {
            if (job.ExpectElementIdValue <= 0)
            {
                throw new InvalidOperationException("job.expect_element_id_value is required in verify mode");
            }

            result["expected_element_id_value"] = job.ExpectElementIdValue;
            VerifyWall(document, new ElementId(job.ExpectElementIdValue), "external_verify_run");
        });

        Step("activate-standby-document", () => app.OpenAndActivateDocument(job.StandbyRvt));
        Step("close-document-final", () => document.Close(false));
    }

    private long reportedElementIdValue;

    private ElementId InvokeExternalCommand()
    {
        // The host invokes the exact compiled wall contract directly. Revit does
        // not expose a public ExternalCommandData constructor, so the shared
        // LabWallCore entry point is the only way to run the same code path
        // without a ribbon click or an MCP bridge.
        var document = app.ActiveUIDocument?.Document
            ?? throw new InvalidOperationException("host lost the active document before the command ran");

        var message = string.Empty;

        var watch = Stopwatch.StartNew();
        var commandResult = Amanda.ToolLab.CustomApi.LabWallCore.Execute(app, document, ref message);
        var elapsed = watch.ElapsedMilliseconds;

        result["command_result"] = commandResult.ToString();
        result["command_message"] = message;
        result["command_ms"] = elapsed;
        reportedElementIdValue = ExtractElementIdValue(message);
        result["command_reported_element_id_value_parsed"] = reportedElementIdValue;

        if (commandResult != Result.Succeeded)
        {
            throw new InvalidOperationException(
                $"LabWallCore returned {commandResult}: {message}");
        }

        return ElementId.InvalidElementId;
    }

    private static long ExtractElementIdValue(string message)
    {
        if (string.IsNullOrWhiteSpace(message))
        {
            return 0L;
        }

        var marker = "ElementId.Value=";
        var index = message.IndexOf(marker, StringComparison.Ordinal);
        if (index < 0)
        {
            return 0L;
        }

        var digits = new string(message
            .Substring(index + marker.Length)
            .TakeWhile(char.IsDigit)
            .ToArray());

        return long.TryParse(digits, out var value) ? value : 0L;
    }

    private void PrepareKnownLevel(Document document)
    {
        var existing = new FilteredElementCollector(document)
            .OfClass(typeof(Level))
            .WhereElementIsNotElementType()
            .Cast<Level>()
            .FirstOrDefault(candidate =>
                string.Equals(candidate.Name, KnownLevelName, StringComparison.OrdinalIgnoreCase));

        if (existing != null)
        {
            result["fixture_level_preexisting_id"] = existing.Id.Value;
            result["fixture_level_created"] = false;
            return;
        }

        using var transaction = new Transaction(document, "P02-T16 fixture: ensure " + KnownLevelName);
        transaction.Start();
        var level = Level.Create(document, 0.0);
        level.Name = KnownLevelName;
        transaction.Commit();

        result["fixture_level_created"] = true;
        result["fixture_level_created_id"] = level.Id.Value;
    }

    private static HashSet<long> CollectWallIds(Document document) =>
        new FilteredElementCollector(document)
            .OfClass(typeof(Wall))
            .WhereElementIsNotElementType()
            .Select(element => element.Id.Value)
            .ToHashSet();

    private void VerifyWall(Document document, ElementId wallId, string phase)
    {
        var wall = document.GetElement(wallId) as Wall
            ?? throw new InvalidOperationException(
                $"wall ElementId.Value={wallId.Value} could not be re-queried ({phase})");

        var boundingBox = wall.get_BoundingBox(null)
            ?? throw new InvalidOperationException(
                $"wall ElementId.Value={wallId.Value} has no bounding box ({phase})");

        var lengthMetres = UnitUtils.ConvertFromInternalUnits(
            boundingBox.Max.X - boundingBox.Min.X,
            UnitTypeId.Meters);
        var heightMetres = UnitUtils.ConvertFromInternalUnits(
            boundingBox.Max.Z - boundingBox.Min.Z,
            UnitTypeId.Meters);

        var geometryMatches =
            Math.Abs(lengthMetres - ExpectedLengthMetres) <= ToleranceMetres &&
            Math.Abs(heightMetres - ExpectedHeightMetres) <= ToleranceMetres;

        var wallTypeName = document.GetElement(wall.GetTypeId())?.Name ?? "unknown";
        var levelName = document.GetElement(wall.LevelId)?.Name ?? "unknown";

        var record = new Dictionary<string, object?>
        {
            ["phase"] = phase,
            ["element_id_value"] = wallId.Value,
            ["length_m"] = Math.Round(lengthMetres, 4),
            ["height_m"] = Math.Round(heightMetres, 4),
            ["wall_type"] = wallTypeName,
            ["level"] = levelName,
            ["geometry_matches_contract"] = geometryMatches,
        };

        var verifications = result.TryGetValue("verifications", out var existing) &&
            existing is List<Dictionary<string, object?>> list
                ? list
                : new List<Dictionary<string, object?>>();
        verifications.Add(record);
        result["verifications"] = verifications;

        if (!geometryMatches)
        {
            throw new InvalidOperationException(
                $"geometry mismatch ({phase}): length={lengthMetres:0.###} m height={heightMetres:0.###} m");
        }
    }

    private void Step(string name, Action action)
    {
        var watch = Stopwatch.StartNew();
        try
        {
            action();
            Record(name, "PASS", watch.ElapsedMilliseconds, null);
        }
        catch (Exception exception)
        {
            Record(name, "FAIL", watch.ElapsedMilliseconds, exception.Message);
            throw;
        }
    }

    private void Record(string name, string status, long durationMs, string? detail)
    {
        steps.Add(new Dictionary<string, object?>
        {
            ["name"] = name,
            ["status"] = status,
            ["duration_ms"] = durationMs,
            ["detail"] = detail,
        });
        LabHostFiles.Journal($"step {name}: {status} ({durationMs} ms) {detail}");
    }

    private JobSpec LoadJob()
    {
        var jobPath = LabHostFiles.JobPath;
        if (!File.Exists(jobPath))
        {
            throw new FileNotFoundException("job file missing", jobPath);
        }

        var parsed = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(
            File.ReadAllText(jobPath)) ?? new Dictionary<string, JsonElement>();

        string GetString(string key, string fallback) =>
            parsed.TryGetValue(key, out var value) && value.ValueKind == JsonValueKind.String
                ? value.GetString() ?? fallback
                : fallback;

        long GetLong(string key) =>
            parsed.TryGetValue(key, out var value) && value.ValueKind == JsonValueKind.Number
                ? value.GetInt64()
                : 0L;

        int GetInt(string key) =>
            parsed.TryGetValue(key, out var value) && value.ValueKind == JsonValueKind.Number
                ? value.GetInt32()
                : 0;

        var resultPathFromJob = GetString("result_path", string.Empty);

        return new JobSpec(
            GetString("mode", "create"),
            GetString("work_rvt", string.Empty),
            GetString("standby_rvt", string.Empty),
            string.IsNullOrWhiteSpace(resultPathFromJob) ? LabHostFiles.DefaultResultPath : resultPathFromJob,
            GetString("status_path", LabHostFiles.StatusPath),
            GetLong("expect_element_id_value"),
            GetInt("expected_pid"),
            GetString("env_token", string.Empty));
    }

    private void WriteResult()
    {
        try
        {
            var options = new JsonSerializerOptions { WriteIndented = true };
            File.WriteAllText(resultPath, JsonSerializer.Serialize(result, options));
            LabHostFiles.Journal("result written to " + resultPath);
        }
        catch (Exception exception)
        {
            LabHostFiles.Journal("result write failed: " + exception);
        }
    }

    /// <summary>
    /// Deliberately does nothing unless the job explicitly asks for it.
    ///
    /// An earlier revision unconditionally posted ExitRevit. When the same lab
    /// add-in happened to be loaded in another Revit instance that had the
    /// assembly present in the shared add-ins folder, that post closed a session
    /// this add-in does not own. Closing Revit is now the runner's decision, made
    /// only after it proves it started the process itself.
    /// </summary>
    private void TryExitRevit()
    {
        LabHostFiles.Journal("exit revit not requested by job; leaving the process alone");
    }
}
