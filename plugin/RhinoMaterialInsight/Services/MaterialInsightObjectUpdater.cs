using Rhino;
using Rhino.DocObjects;
using RhinoMaterialInsight.Models;

namespace RhinoMaterialInsight.Services;

public sealed class MaterialInsightObjectUpdater
{
    public bool ApplyApprovedValues(
        RhinoDoc doc,
        RhinoObject rhinoObject,
        RecommendationResult recommendation,
        Dictionary<string, object?> editedValues)
    {
        var attributes = rhinoObject.Attributes.Duplicate();

        if (editedValues.TryGetValue("material", out var material) && material is not null)
        {
            attributes.SetUserString("material", material.ToString());
        }

        if (editedValues.TryGetValue("thickness_mm", out var thickness) && thickness is not null)
        {
            attributes.SetUserString("thickness_mm", thickness.ToString());
        }

        attributes.SetUserString("review_status", "completed");
        attributes.SetUserString("last_review_id", recommendation.RecommendationId);
        attributes.SetUserString("last_review_summary", recommendation.Summary);

        var updated = doc.Objects.ModifyAttributes(rhinoObject, attributes, true);
        if (updated)
        {
            doc.Views.Redraw();
        }

        return updated;
    }
}
