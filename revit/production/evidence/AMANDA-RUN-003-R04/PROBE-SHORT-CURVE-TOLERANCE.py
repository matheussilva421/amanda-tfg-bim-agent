document = globals().get('doc') or globals().get('document') or globals().get('__document__')
if document is None:
    raise RuntimeError('active document missing')
tol_ft = float(document.Application.ShortCurveTolerance)
__output__ = {
    'status': 'self_reported_verified',
    'short_curve_tolerance_ft': tol_ft,
    'short_curve_tolerance_m': tol_ft / 3.280839895013123,
    'verification': {
        'checked': True,
        'evidence': ['Document.Application.ShortCurveTolerance read from active Revit document'],
    },
}
