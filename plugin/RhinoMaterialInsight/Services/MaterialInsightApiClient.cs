using System.Net.Http.Json;
using System.Text.Json;
using RhinoMaterialInsight.Models;

namespace RhinoMaterialInsight.Services;

public sealed class MaterialInsightApiClient
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        WriteIndented = false
    };

    private readonly HttpClient _httpClient;

    public MaterialInsightApiClient()
        : this(new HttpClient
        {
            BaseAddress = new Uri("http://localhost:8000"),
            Timeout = TimeSpan.FromSeconds(8)
        })
    {
    }

    public MaterialInsightApiClient(HttpClient httpClient)
    {
        _httpClient = httpClient;
    }

    public async Task<RecommendationResult> ReviewObjectAsync(
        ReviewObjectRequest request,
        CancellationToken cancellationToken = default)
    {
        try
        {
            using var response = await _httpClient.PostAsJsonAsync(
                "/api/v1/review-object",
                request,
                JsonOptions,
                cancellationToken);

            response.EnsureSuccessStatusCode();
            var recommendation = await response.Content.ReadFromJsonAsync<RecommendationResult>(
                JsonOptions,
                cancellationToken);

            return recommendation ?? throw new InvalidOperationException("Backend returned an empty recommendation.");
        }
        catch (TaskCanceledException exception) when (!cancellationToken.IsCancellationRequested)
        {
            throw new TimeoutException(
                "Material Insight backend did not respond within 8 seconds. Check that FastAPI is running at http://localhost:8000.",
                exception);
        }
    }

    public async Task SaveReviewActionAsync(
        ReviewActionRequest request,
        CancellationToken cancellationToken = default)
    {
        using var response = await _httpClient.PostAsJsonAsync(
            "/api/v1/review-actions",
            request,
            JsonOptions,
            cancellationToken);

        response.EnsureSuccessStatusCode();
    }
}
