using System.Text.Json.Serialization;

namespace RhinoMaterialInsight.Models;

public sealed record ProjectContext(
    [property: JsonPropertyName("project_id")] string ProjectId,
    [property: JsonPropertyName("project_type")] string? ProjectType,
    [property: JsonPropertyName("design_stage")] string? DesignStage,
    [property: JsonPropertyName("building_use")] string? BuildingUse,
    [property: JsonPropertyName("region")] string? Region,
    [property: JsonPropertyName("priority")] string? Priority);

public sealed record GeometrySummary(
    [property: JsonPropertyName("object_kind")] string? ObjectKind,
    [property: JsonPropertyName("length_mm")] double? LengthMm,
    [property: JsonPropertyName("area_m2")] double? AreaM2,
    [property: JsonPropertyName("volume_m3")] double? VolumeM3,
    [property: JsonPropertyName("bbox")] Dictionary<string, object?> BBox);

public sealed record RhinoObjectInput(
    [property: JsonPropertyName("object_id")] string ObjectId,
    [property: JsonPropertyName("object_type")] string? ObjectType,
    [property: JsonPropertyName("layer")] string? Layer,
    [property: JsonPropertyName("name")] string? Name,
    [property: JsonPropertyName("material")] string? Material,
    [property: JsonPropertyName("thickness_mm")] double? ThicknessMm,
    [property: JsonPropertyName("space_type")] string? SpaceType,
    [property: JsonPropertyName("review_status")] string? ReviewStatus,
    [property: JsonPropertyName("geometry")] GeometrySummary Geometry,
    [property: JsonPropertyName("user_attributes")] Dictionary<string, object?> UserAttributes);

public sealed record RhinoObjectSummary(
    [property: JsonPropertyName("object_id")] string ObjectId,
    [property: JsonPropertyName("rhino_id")] string? RhinoId,
    [property: JsonPropertyName("name")] string? Name,
    [property: JsonPropertyName("layer")] string? Layer,
    [property: JsonPropertyName("object_kind")] string? ObjectKind,
    [property: JsonPropertyName("material")] string? Material,
    [property: JsonPropertyName("object_type")] string? ObjectType,
    [property: JsonPropertyName("space_type")] string? SpaceType,
    [property: JsonPropertyName("thickness_mm")] double? ThicknessMm,
    [property: JsonPropertyName("review_status")] string? ReviewStatus,
    [property: JsonPropertyName("is_visible")] bool IsVisible,
    [property: JsonPropertyName("is_locked")] bool IsLocked,
    [property: JsonPropertyName("bbox")] Dictionary<string, object?> BBox,
    [property: JsonPropertyName("user_attributes")] Dictionary<string, object?> UserAttributes);

public sealed record RhinoObjectSyncRequest(
    [property: JsonPropertyName("project")] ProjectContext Project,
    [property: JsonPropertyName("objects")] IReadOnlyList<RhinoObjectSummary> Objects);

public sealed record RhinoObjectSyncResponse(
    [property: JsonPropertyName("project_id")] string ProjectId,
    [property: JsonPropertyName("object_count")] int ObjectCount);

public sealed record RhinoSelectionState(
    [property: JsonPropertyName("project_id")] string ProjectId,
    [property: JsonPropertyName("object_id")] string? ObjectId);
