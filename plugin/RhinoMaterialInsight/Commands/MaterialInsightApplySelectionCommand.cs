using Rhino;
using Rhino.Commands;
using Rhino.DocObjects;
using RhinoMaterialInsight.Services;

namespace RhinoMaterialInsight.Commands;

public sealed class MaterialInsightApplySelectionCommand : Command
{
    private readonly MaterialInsightObjectInspector _objectInspector = new();
    private readonly MaterialInsightApiClient _apiClient = new();

    public override string EnglishName => "MaterialInsightApplySelection";

    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        var project = _objectInspector.BuildProjectContext(doc);
        RhinoApp.WriteLine(
            $"Material Insight: loading frontend selection for project {project.ProjectId} in background...");

        _ = ApplySelectionInBackgroundAsync(doc, project.ProjectId);
        return Result.Success;
    }

    private async Task ApplySelectionInBackgroundAsync(RhinoDoc doc, string projectId)
    {
        try
        {
            var selection = await _apiClient.GetRhinoSelectionAsync(projectId);
            RhinoApp.InvokeOnUiThread((Action)(() =>
            {
                ApplySelectionOnUiThread(doc, selection.ObjectId);
            }));
        }
        catch (Exception exception)
        {
            RhinoApp.InvokeOnUiThread((Action)(() =>
            {
                RhinoApp.WriteLine($"Material Insight apply selection failed: {exception.Message}");
            }));
        }
    }

    private void ApplySelectionOnUiThread(RhinoDoc doc, string? objectId)
    {
        if (string.IsNullOrWhiteSpace(objectId))
        {
            RhinoApp.WriteLine("Material Insight: no frontend object selection is available.");
            return;
        }

        var rhinoObject = FindObject(doc, objectId);
        if (rhinoObject is null)
        {
            RhinoApp.WriteLine($"Material Insight: object '{objectId}' was not found in the active Rhino document.");
            return;
        }

        doc.Objects.UnselectAll();
        rhinoObject.Select(true);
        ZoomToObject(doc, rhinoObject);
        doc.Views.Redraw();

        RhinoApp.WriteLine($"Material Insight: selected Rhino object '{objectId}'.");
    }

    private RhinoObject? FindObject(RhinoDoc doc, string objectId)
    {
        if (Guid.TryParse(objectId, out var guid))
        {
            var byGuid = doc.Objects.FindId(guid);
            if (byGuid is not null)
            {
                return byGuid;
            }
        }

        foreach (var rhinoObject in doc.Objects)
        {
            if (rhinoObject is null)
            {
                continue;
            }

            var attributes = rhinoObject.Attributes;
            if (string.Equals(attributes.GetUserString("material_insight_object_id"), objectId, StringComparison.OrdinalIgnoreCase)
                || string.Equals(rhinoObject.Id.ToString(), objectId, StringComparison.OrdinalIgnoreCase)
                || string.Equals(attributes.Name, objectId, StringComparison.OrdinalIgnoreCase))
            {
                return rhinoObject;
            }
        }

        return null;
    }

    private static void ZoomToObject(RhinoDoc doc, RhinoObject rhinoObject)
    {
        var view = doc.Views.ActiveView;
        if (view is null)
        {
            return;
        }

        var bbox = rhinoObject.Geometry.GetBoundingBox(true);
        if (!bbox.IsValid)
        {
            return;
        }

        view.ActiveViewport.ZoomBoundingBox(bbox);
    }
}
