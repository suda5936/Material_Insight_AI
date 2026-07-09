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

    public async Task<RhinoObjectSyncResponse> SyncRhinoObjectsAsync(
        RhinoObjectSyncRequest request,
        CancellationToken cancellationToken = default)
    {
        try
        {
            using var response = await _httpClient.PostAsJsonAsync(
                "/api/v1/rhino/objects",
                request,
                JsonOptions,
                cancellationToken);

            response.EnsureSuccessStatusCode();
            var syncResponse = await response.Content.ReadFromJsonAsync<RhinoObjectSyncResponse>(
                JsonOptions,
                cancellationToken);

            return syncResponse ?? throw new InvalidOperationException("Backend returned an empty sync response.");
        }
        catch (TaskCanceledException exception) when (!cancellationToken.IsCancellationRequested)
        {
            throw new TimeoutException(
                "Construction CP Recovery backend did not respond within 8 seconds. Check that FastAPI is running at http://localhost:8000.",
                exception);
        }
    }

    public async Task<RhinoSelectionState> GetRhinoSelectionAsync(
        string projectId,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var path = $"/api/v1/rhino/selection?project_id={Uri.EscapeDataString(projectId)}";
            var selection = await _httpClient.GetFromJsonAsync<RhinoSelectionState>(
                path,
                JsonOptions,
                cancellationToken);

            return selection ?? throw new InvalidOperationException("Backend returned an empty selection state.");
        }
        catch (TaskCanceledException exception) when (!cancellationToken.IsCancellationRequested)
        {
            throw new TimeoutException(
                "Construction CP Recovery backend did not respond within 8 seconds. Check that FastAPI is running at http://localhost:8000.",
                exception);
        }
    }
}
