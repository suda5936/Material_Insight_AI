using Rhino;
using Rhino.Commands;
using Rhino.DocObjects;
using Rhino.Input;
using RhinoMaterialInsight.Models;
using RhinoMaterialInsight.Panels;
using RhinoMaterialInsight.Services;

namespace RhinoMaterialInsight.Commands;

public sealed class MaterialInsightReviewCommand : Command
{
    private readonly MaterialInsightObjectInspector _objectInspector = new();
    private readonly MaterialInsightApiClient _apiClient = new();
    private readonly MaterialInsightReviewPanel _reviewPanel = new();

    public override string EnglishName => "MaterialInsightReview";

    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        var getResult = RhinoGet.GetOneObject(
            "Select an object to review with Material Insight",
            false,
            ObjectType.AnyObject,
            out var objRef);

        if (getResult != Result.Success)
        {
            return getResult;
        }

        var rhinoObject = objRef.Object();
        if (rhinoObject is null)
        {
            RhinoApp.WriteLine("Material Insight: no Rhino object was selected.");
            return Result.Failure;
        }

        var request = _objectInspector.BuildReviewRequest(doc, rhinoObject);
        _reviewPanel.ShowObjectSummary(request.Object);
        RhinoApp.WriteLine("Material Insight: sending review request to backend in background...");

        _ = ReviewObjectInBackgroundAsync(request);

        return Result.Success;
    }

    private async Task ReviewObjectInBackgroundAsync(ReviewObjectRequest request)
    {
        try
        {
            var recommendation = await _apiClient.ReviewObjectAsync(request);
            RhinoApp.InvokeOnUiThread((Action)(() =>
            {
                RhinoApp.WriteLine("Material Insight: backend response received.");
                _reviewPanel.ShowRecommendation(recommendation);
            }));
        }
        catch (Exception exception)
        {
            RhinoApp.InvokeOnUiThread((Action)(() =>
            {
                _reviewPanel.ShowError(exception.Message);
            }));
        }
    }
}
