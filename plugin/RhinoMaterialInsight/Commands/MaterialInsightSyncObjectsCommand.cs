using Rhino;
using Rhino.Commands;
using Rhino.DocObjects;
using RhinoMaterialInsight.Models;
using RhinoMaterialInsight.Services;

namespace RhinoMaterialInsight.Commands;

public sealed class MaterialInsightSyncObjectsCommand : Command
{
    private readonly MaterialInsightObjectInspector _objectInspector = new();
    private readonly MaterialInsightApiClient _apiClient = new();

    public override string EnglishName => "MaterialInsightSyncObjects";

    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        var objects = new List<RhinoObjectSummary>();
        foreach (var rhinoObject in doc.Objects)
        {
            if (rhinoObject is null)
            {
                continue;
            }

            var attributes = rhinoObject.Attributes;
            if (!attributes.Visible || attributes.Mode == ObjectMode.Hidden)
            {
                continue;
            }

            objects.Add(_objectInspector.BuildObjectSummary(doc, rhinoObject));
        }

        var request = new RhinoObjectSyncRequest(
            Project: _objectInspector.BuildProjectContext(doc),
            Objects: objects);

        RhinoApp.WriteLine($"Material Insight: syncing {objects.Count} Rhino objects to backend in background...");
        _ = SyncObjectsInBackgroundAsync(request);

        return Result.Success;
    }

    private async Task SyncObjectsInBackgroundAsync(RhinoObjectSyncRequest request)
    {
        try
        {
            var response = await _apiClient.SyncRhinoObjectsAsync(request);
            RhinoApp.InvokeOnUiThread((Action)(() =>
            {
                RhinoApp.WriteLine(
                    $"Material Insight: synced {response.ObjectCount} objects for project {response.ProjectId}.");
            }));
        }
        catch (Exception exception)
        {
            RhinoApp.InvokeOnUiThread((Action)(() =>
            {
                RhinoApp.WriteLine($"Material Insight sync failed: {exception.Message}");
            }));
        }
    }
}
