using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using RhinoMaterialInsight.Models;

namespace RhinoMaterialInsight.Services;

public sealed class MaterialInsightObjectInspector
{
    private static readonly HashSet<string> ReservedUserStringKeys = new(StringComparer.OrdinalIgnoreCase)
    {
        "object_type",
        "space_type",
        "thickness_mm",
        "review_status",
        "material"
    };

    public RhinoObjectInput BuildObjectInput(RhinoDoc doc, RhinoObject rhinoObject)
    {
        var attributes = rhinoObject.Attributes;
        var geometry = rhinoObject.Geometry;

        return new RhinoObjectInput(
            ObjectId: ResolveObjectId(attributes, rhinoObject),
            ObjectType: ReadString(attributes, "object_type"),
            Layer: ResolveLayerName(doc, attributes),
            Name: attributes.Name,
            Material: ReadString(attributes, "material") ?? ResolveMaterialName(doc, rhinoObject),
            ThicknessMm: ReadDouble(attributes, "thickness_mm"),
            SpaceType: ReadString(attributes, "space_type"),
            ReviewStatus: ReadString(attributes, "review_status") ?? "pending",
            Geometry: BuildGeometrySummary(geometry),
            UserAttributes: ReadUserAttributes(attributes));
    }

    public RhinoObjectSummary BuildObjectSummary(RhinoDoc doc, RhinoObject rhinoObject)
    {
        var input = BuildObjectInput(doc, rhinoObject);
        var attributes = rhinoObject.Attributes;

        return new RhinoObjectSummary(
            ObjectId: input.ObjectId,
            RhinoId: rhinoObject.Id.ToString(),
            Name: input.Name,
            Layer: input.Layer,
            ObjectKind: input.Geometry.ObjectKind,
            Material: input.Material,
            ObjectType: input.ObjectType,
            SpaceType: input.SpaceType,
            ThicknessMm: input.ThicknessMm,
            ReviewStatus: input.ReviewStatus,
            IsVisible: attributes.Visible,
            IsLocked: attributes.Mode == ObjectMode.Locked,
            BBox: input.Geometry.BBox,
            UserAttributes: input.UserAttributes);
    }

    public ProjectContext BuildProjectContext(RhinoDoc doc)
    {
        return new ProjectContext(
            ProjectId: ReadDocumentString(doc, "project_id") ?? "RHINO-PROJECT",
            ProjectType: ReadDocumentString(doc, "project_type") ?? "interior",
            DesignStage: ReadDocumentString(doc, "design_stage") ?? "basic_design",
            BuildingUse: ReadDocumentString(doc, "building_use") ?? "office",
            Region: ReadDocumentString(doc, "region") ?? "KR",
            Priority: ReadDocumentString(doc, "priority") ?? "performance");
    }

    private static string ResolveObjectId(ObjectAttributes attributes, RhinoObject rhinoObject)
    {
        return attributes.GetUserString("material_insight_object_id")
            ?? attributes.Name
            ?? rhinoObject.Id.ToString();
    }

    private static string? ResolveLayerName(RhinoDoc doc, ObjectAttributes attributes)
    {
        if (attributes.LayerIndex < 0 || attributes.LayerIndex >= doc.Layers.Count)
        {
            return null;
        }

        return doc.Layers[attributes.LayerIndex].FullPath;
    }

    private static string? ResolveMaterialName(RhinoDoc doc, RhinoObject rhinoObject)
    {
        var material = rhinoObject.GetMaterial(true);
        if (!string.IsNullOrWhiteSpace(material?.Name))
        {
            return material.Name;
        }

        var attributes = rhinoObject.Attributes;
        if (attributes.MaterialIndex >= 0 && attributes.MaterialIndex < doc.Materials.Count)
        {
            return doc.Materials[attributes.MaterialIndex].Name;
        }

        return null;
    }

    private static GeometrySummary BuildGeometrySummary(GeometryBase geometry)
    {
        var bbox = geometry.GetBoundingBox(true);
        var bboxValues = new Dictionary<string, object?>
        {
            ["min"] = new[] { bbox.Min.X, bbox.Min.Y, bbox.Min.Z },
            ["max"] = new[] { bbox.Max.X, bbox.Max.Y, bbox.Max.Z }
        };

        return new GeometrySummary(
            ObjectKind: geometry.ObjectType.ToString(),
            LengthMm: TryGetLengthMm(geometry),
            AreaM2: TryGetAreaM2(geometry),
            VolumeM3: TryGetVolumeM3(geometry),
            BBox: bboxValues);
    }

    private static double? TryGetLengthMm(GeometryBase geometry)
    {
        return geometry switch
        {
            Curve curve => curve.GetLength(),
            _ => null
        };
    }

    private static double? TryGetAreaM2(GeometryBase geometry)
    {
        var massProperties = geometry switch
        {
            Brep brep => AreaMassProperties.Compute(brep),
            Mesh mesh => AreaMassProperties.Compute(mesh),
            Surface surface => AreaMassProperties.Compute(surface),
            _ => null
        };
        return massProperties is null ? null : massProperties.Area / 1_000_000.0;
    }

    private static double? TryGetVolumeM3(GeometryBase geometry)
    {
        var massProperties = geometry switch
        {
            Brep brep => VolumeMassProperties.Compute(brep),
            Mesh mesh => VolumeMassProperties.Compute(mesh),
            _ => null
        };
        return massProperties is null ? null : massProperties.Volume / 1_000_000_000.0;
    }

    private static Dictionary<string, object?> ReadUserAttributes(ObjectAttributes attributes)
    {
        var values = new Dictionary<string, object?>();
        var strings = attributes.GetUserStrings();
        if (strings is null)
        {
            return values;
        }

        foreach (var key in strings.AllKeys)
        {
            if (string.IsNullOrWhiteSpace(key))
            {
                continue;
            }

            if (ReservedUserStringKeys.Contains(key))
            {
                continue;
            }

            values[key] = ConvertUserStringValue(strings[key]);
        }

        return values;
    }

    private static object? ConvertUserStringValue(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return null;
        }

        if (bool.TryParse(value, out var booleanValue))
        {
            return booleanValue;
        }

        if (double.TryParse(value, out var doubleValue))
        {
            return doubleValue;
        }

        return value;
    }

    private static string? ReadString(ObjectAttributes attributes, string key)
    {
        var value = attributes.GetUserString(key);
        return string.IsNullOrWhiteSpace(value) ? null : value;
    }

    private static double? ReadDouble(ObjectAttributes attributes, string key)
    {
        var value = attributes.GetUserString(key);
        return double.TryParse(value, out var doubleValue) ? doubleValue : null;
    }

    private static string? ReadDocumentString(RhinoDoc doc, string key)
    {
        var value = doc.Strings.GetValue("MaterialInsight", key);
        return string.IsNullOrWhiteSpace(value) ? null : value;
    }
}
