using Rhino;
using RhinoMaterialInsight.Models;

namespace RhinoMaterialInsight.Panels;

public sealed class MaterialInsightReviewPanel
{
    public void ShowObjectSummary(DesignObjectInput designObject)
    {
        RhinoApp.WriteLine(
            $"Material Insight object: {designObject.ObjectId}, " +
            $"type={designObject.ObjectType ?? "missing"}, " +
            $"space={designObject.SpaceType ?? "missing"}, " +
            $"material={designObject.Material ?? "missing"}");
    }

    public void ShowRecommendation(RecommendationResult recommendation)
    {
        RhinoApp.WriteLine("Material Insight recommendation");
        RhinoApp.WriteLine($"- status: {recommendation.Status}");
        RhinoApp.WriteLine($"- severity: {recommendation.Severity}");
        RhinoApp.WriteLine($"- required_action: {recommendation.RequiredAction}");
        RhinoApp.WriteLine($"- summary: {recommendation.Summary}");

        if (recommendation.Sources.Count == 0)
        {
            RhinoApp.WriteLine("- sources: none");
            return;
        }

        RhinoApp.WriteLine("- sources:");
        foreach (var source in recommendation.Sources)
        {
            RhinoApp.WriteLine($"  - {source.DocumentId}: {source.Title} ({source.Section})");
        }
    }

    public void ShowError(string message)
    {
        RhinoApp.WriteLine($"Material Insight error: {message}");
    }
}
