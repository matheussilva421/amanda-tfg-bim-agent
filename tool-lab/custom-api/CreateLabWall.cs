#nullable enable

using System;
using System.Diagnostics;
using System.Linq;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace Amanda.ToolLab.CustomApi;

/// <summary>
/// Minimal independent Revit API fallback proof for P02-T16.
///
/// This type is the thin <see cref="IExternalCommand"/> entry point that Revit
/// invokes from the Add-Ins ribbon. The command logic itself lives in
/// <see cref="LabWallCore"/> so the same compiled code path can also be driven
/// by an autonomous test host without any MCP bridge in between.
/// </summary>
[Transaction(TransactionMode.Manual)]
public sealed class CreateLabWall : IExternalCommand
{
    public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
    {
        var application = commandData?.Application;
        var document = application?.ActiveUIDocument?.Document;
        return LabWallCore.Execute(application, document, ref message);
    }
}

/// <summary>
/// The fail-closed wall creation contract.
///
/// The core deliberately resolves every prerequisite before opening its
/// transaction. Any missing prerequisite or failed verification returns
/// <see cref="Result.Failed"/>; no best-effort level/type selection is attempted.
/// </summary>
public static class LabWallCore
{
    private const string KnownLevelName = "Level 1";
    private const double WallLengthMetres = 5.0;
    private const double WallHeightMetres = 3.0;
    private const double VerificationToleranceMetres = 0.01;
    private const string TransactionName = "P02-T16 Custom API fallback: create one lab wall";

    public static Result Execute(UIApplication? application, Document? document, ref string message)
    {
        try
        {
            if (document == null)
                throw new InvalidOperationException("An active Revit document is required.");

            if (document.IsFamilyDocument)
                throw new InvalidOperationException("A project document is required; family documents are not supported.");

            // Resolve all prerequisites before the transaction so a failed lookup
            // cannot leave a partially created model element.
            var level = FindKnownLevel(document);
            var wallType = FindBasicWallType(document);
            var lengthInternal = MetresToInternalUnits(WallLengthMetres);
            var heightInternal = MetresToInternalUnits(WallHeightMetres);

            var wallId = CreateAndVerifyWall(
                document,
                level,
                wallType,
                lengthInternal,
                heightInternal);

            var resultMessage =
                $"P02-T16 command result: created wall ElementId.Value={wallId.Value} " +
                $"on '{level.Name}' with length={WallLengthMetres:0.##} m and height={WallHeightMetres:0.##} m.";

            Trace.WriteLine(resultMessage);
            try
            {
                application?.Application.WriteJournalComment(resultMessage, true);
            }
            catch
            {
                // Journaling is best effort; it must not change the outcome.
            }

            message = resultMessage;
            return Result.Succeeded;
        }
        catch (InvalidOperationException exception)
        {
            message = $"P02-T16 FAILED closed: {exception.Message}";
            Trace.WriteLine(message);
            return Result.Failed;
        }
        catch (Exception exception)
        {
            message = $"P02-T16 FAILED closed with unexpected Revit API error: {exception.Message}";
            Trace.WriteLine($"{message}\n{exception}");
            return Result.Failed;
        }
    }

    private static Level FindKnownLevel(Document document)
    {
        var level = new FilteredElementCollector(document)
            .OfClass(typeof(Level))
            .WhereElementIsNotElementType()
            .Cast<Level>()
            .SingleOrDefault(candidate =>
                string.Equals(candidate.Name, KnownLevelName, StringComparison.OrdinalIgnoreCase));

        return level
            ?? throw new InvalidOperationException(
                $"Required level '{KnownLevelName}' was not found. The command will not create a wall.");
    }

    private static WallType FindBasicWallType(Document document)
    {
        var wallType = new FilteredElementCollector(document)
            .OfClass(typeof(WallType))
            .WhereElementIsElementType()
            .Cast<WallType>()
            .FirstOrDefault(candidate => candidate.Kind == WallKind.Basic);

        return wallType
            ?? throw new InvalidOperationException(
                "No basic WallType is available in the active project. The command will not create a wall.");
    }

    private static double MetresToInternalUnits(double metres)
    {
        if (metres <= 0.0)
            throw new InvalidOperationException("Wall dimensions must be positive.");

        return UnitUtils.ConvertToInternalUnits(metres, UnitTypeId.Meters);
    }

    private static ElementId CreateAndVerifyWall(
        Document document,
        Level level,
        WallType wallType,
        double lengthInternal,
        double heightInternal)
    {
        using var transaction = new Transaction(document, TransactionName);
        var transactionStarted = false;

        try
        {
            transaction.Start();
            transactionStarted = true;

            var basePoint = new XYZ(0.0, 0.0, level.Elevation);
            var endPoint = new XYZ(lengthInternal, 0.0, level.Elevation);
            var baseline = Line.CreateBound(basePoint, endPoint);
            var wall = Wall.Create(
                document,
                baseline,
                wallType.Id,
                level.Id,
                heightInternal,
                0.0,
                false,
                false);

            if (wall == null || wall.Id == ElementId.InvalidElementId)
                throw new InvalidOperationException("Revit did not return a valid ElementId for the wall.");

            // Geometry is not computed until the model regenerates, so a freshly
            // created wall has no bounding box yet. Regenerate inside the
            // transaction so the verification below reads real geometry and a
            // failed check still rolls the wall back.
            document.Regenerate();

            // Re-query through the document before committing. This read is kept
            // separate from the local return value and must pass before mutation
            // can become durable.
            var createdWallId = wall.Id;
            var createdWallIdValue = createdWallId.Value;
            var rereadWall = document.GetElement(createdWallId) as Wall
                ?? throw new InvalidOperationException(
                    $"Revit could not re-query wall ElementId.Value={createdWallIdValue}.");
            var boundingBox = rereadWall.get_BoundingBox(null)
                ?? throw new InvalidOperationException(
                    $"Wall ElementId.Value={createdWallIdValue} has no bounding box to verify.");

            VerifyBoundingBox(boundingBox, lengthInternal, heightInternal, createdWallIdValue);

            if (transaction.Commit() != TransactionStatus.Committed)
                throw new InvalidOperationException("Revit did not commit the wall transaction.");

            return createdWallId;
        }
        catch
        {
            if (transactionStarted && transaction.GetStatus() == TransactionStatus.Started)
                transaction.RollBack();

            throw;
        }
    }

    private static void VerifyBoundingBox(
        BoundingBoxXYZ boundingBox,
        double expectedLengthInternal,
        double expectedHeightInternal,
        long elementIdValue)
    {
        var toleranceInternal = MetresToInternalUnits(VerificationToleranceMetres);
        var actualLengthInternal = boundingBox.Max.X - boundingBox.Min.X;
        var actualHeightInternal = boundingBox.Max.Z - boundingBox.Min.Z;

        if (Math.Abs(actualLengthInternal - expectedLengthInternal) > toleranceInternal ||
            Math.Abs(actualHeightInternal - expectedHeightInternal) > toleranceInternal)
        {
            throw new InvalidOperationException(
                $"Wall ElementId.Value={elementIdValue} failed geometry verification: " +
                $"length={actualLengthInternal:0.###} ft, height={actualHeightInternal:0.###} ft.");
        }
    }
}
