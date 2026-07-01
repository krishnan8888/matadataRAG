using System.Net.Http.Json;
using System.Text.Json;
using MetadataRag.Web.Models;
using Microsoft.AspNetCore.Components.Forms;

namespace MetadataRag.Web.Services;

public interface IRagApiClient
{
    Task<HealthResponse> GetHealthAsync(CancellationToken cancellationToken = default);
    Task<IReadOnlyList<DocumentProfile>> GetDocumentsAsync(CancellationToken cancellationToken = default);
    Task<IngestResponse> IngestAsync(IBrowserFile file, CancellationToken cancellationToken = default);
    Task<QueryResponse> QueryAsync(string query, CancellationToken cancellationToken = default);
    Task<ShutdownResponse> ShutdownAsync(CancellationToken cancellationToken = default);
}

public sealed class RagApiClient(HttpClient httpClient) : IRagApiClient
{
    private const long MaxUploadBytes = 25 * 1024 * 1024;
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    public async Task<HealthResponse> GetHealthAsync(CancellationToken cancellationToken = default) =>
        await GetAsync<HealthResponse>("api/health", cancellationToken);

    public async Task<IReadOnlyList<DocumentProfile>> GetDocumentsAsync(
        CancellationToken cancellationToken = default)
    {
        var response = await GetAsync<DocumentsResponse>("api/documents", cancellationToken);
        return response.Documents;
    }

    public async Task<IngestResponse> IngestAsync(
        IBrowserFile file,
        CancellationToken cancellationToken = default)
    {
        using var content = new MultipartFormDataContent();
        await using var stream = file.OpenReadStream(MaxUploadBytes, cancellationToken);
        using var fileContent = new StreamContent(stream);
        fileContent.Headers.ContentType = new(file.ContentType ?? "application/octet-stream");
        content.Add(fileContent, "file", file.Name);

        using var response = await httpClient.PostAsync("api/ingest", content, cancellationToken);
        return await ReadResponseAsync<IngestResponse>(response, cancellationToken);
    }

    public async Task<QueryResponse> QueryAsync(
        string query,
        CancellationToken cancellationToken = default)
    {
        using var response = await httpClient.PostAsJsonAsync(
            "api/query",
            new QueryRequest(query),
            JsonOptions,
            cancellationToken);
        return await ReadResponseAsync<QueryResponse>(response, cancellationToken);
    }

    public async Task<ShutdownResponse> ShutdownAsync(
        CancellationToken cancellationToken = default)
    {
        using var response = await httpClient.PostAsync(
            "api/shutdown",
            content: null,
            cancellationToken);
        return await ReadResponseAsync<ShutdownResponse>(response, cancellationToken);
    }

    private async Task<T> GetAsync<T>(string path, CancellationToken cancellationToken)
    {
        using var response = await httpClient.GetAsync(path, cancellationToken);
        return await ReadResponseAsync<T>(response, cancellationToken);
    }

    private static async Task<T> ReadResponseAsync<T>(
        HttpResponseMessage response,
        CancellationToken cancellationToken)
    {
        if (response.IsSuccessStatusCode)
        {
            return await response.Content.ReadFromJsonAsync<T>(JsonOptions, cancellationToken)
                ?? throw new InvalidOperationException("The RAG API returned an empty response.");
        }

        var body = await response.Content.ReadAsStringAsync(cancellationToken);
        try
        {
            using var payload = JsonDocument.Parse(body);
            if (payload.RootElement.TryGetProperty("detail", out var detail))
            {
                throw new InvalidOperationException(detail.GetString() ?? body);
            }
        }
        catch (JsonException)
        {
        }

        throw new InvalidOperationException(
            string.IsNullOrWhiteSpace(body)
                ? $"RAG API request failed ({(int)response.StatusCode})."
                : body);
    }
}
