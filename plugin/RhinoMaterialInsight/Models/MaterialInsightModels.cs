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

public sealed record DesignObjectInput(
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

public sealed record ReviewObjectRequest(
    [property: JsonPropertyName("project")] ProjectContext Project,
    [property: JsonPropertyName("object")] DesignObjectInput Object);

public sealed record RetrievedDocument(
    [property: JsonPropertyName("document_id")] string DocumentId,
    [property: JsonPropertyName("title")] string Title,
    [property: JsonPropertyName("chunk_text")] string ChunkText,
    [property: JsonPropertyName("document_type")] string DocumentType,
    [property: JsonPropertyName("score")] double Score,
    [property: JsonPropertyName("section")] string? Section,
    [property: JsonPropertyName("version")] string? Version,
    [property: JsonPropertyName("effective_date")] string? EffectiveDate,
    [property: JsonPropertyName("status")] string Status,
    [property: JsonPropertyName("source")] string? Source);

public sealed record RecommendationResult(
    [property: JsonPropertyName("recommendation_id")] string RecommendationId,
    [property: JsonPropertyName("object_id")] string ObjectId,
    [property: JsonPropertyName("status")] string Status,
    [property: JsonPropertyName("severity")] string Severity,
    [property: JsonPropertyName("summary")] string Summary,
    [property: JsonPropertyName("detected_issues")] IReadOnlyList<string> DetectedIssues,
    [property: JsonPropertyName("material_candidates")] IReadOnlyList<string> MaterialCandidates,
    [property: JsonPropertyName("thickness_guidance")] Dictionary<string, object?> ThicknessGuidance,
    [property: JsonPropertyName("performance_notes")] IReadOnlyList<string> PerformanceNotes,
    [property: JsonPropertyName("required_action")] string RequiredAction,
    [property: JsonPropertyName("confidence")] double Confidence,
    [property: JsonPropertyName("sources")] IReadOnlyList<RetrievedDocument> Sources,
    [property: JsonPropertyName("disclaimers")] IReadOnlyList<string> Disclaimers);

public sealed record ReviewActionRequest(
    [property: JsonPropertyName("recommendation_id")] string RecommendationId,
    [property: JsonPropertyName("object_id")] string? ObjectId,
    [property: JsonPropertyName("user_id")] string UserId,
    [property: JsonPropertyName("action")] string Action,
    [property: JsonPropertyName("edited_values")] Dictionary<string, object?> EditedValues,
    [property: JsonPropertyName("sources")] IReadOnlyList<RetrievedDocument> Sources,
    [property: JsonPropertyName("reason")] string? Reason);
