using System.Text.Json;
using System.Text.Json.Serialization;

namespace MetadataRag.Web.Models;

public sealed record HealthResponse(
    [property: JsonPropertyName("status")] string Status,
    [property: JsonPropertyName("documents")] int Documents);

public sealed record ShutdownResponse(
    [property: JsonPropertyName("status")] string Status,
    [property: JsonPropertyName("unloaded_models")] IReadOnlyList<string> UnloadedModels);

public sealed record DocumentsResponse(
    [property: JsonPropertyName("documents")] IReadOnlyList<DocumentProfile> Documents);

public sealed record DocumentProfile
{
    [JsonPropertyName("document_id")]
    public string DocumentId { get; init; } = "";

    [JsonPropertyName("document_type")]
    public string DocumentType { get; init; } = "";

    [JsonPropertyName("embedding_mode")]
    public string EmbeddingMode { get; init; } = "";

    [JsonPropertyName("retrieval_modes")]
    public IReadOnlyList<string> RetrievalModes { get; init; } = [];

    [JsonPropertyName("metadata_score")]
    public double MetadataScore { get; init; }
}

public sealed record IngestResponse
{
    [JsonPropertyName("document_id")]
    public string DocumentId { get; init; } = "";

    [JsonPropertyName("filename")]
    public string Filename { get; init; } = "";

    [JsonPropertyName("metadata")]
    public JsonElement Metadata { get; init; }

    public string EmbeddingMode =>
        Metadata.ValueKind == JsonValueKind.Object
        && Metadata.TryGetProperty("embedding_mode", out var mode)
            ? mode.GetString() ?? "ready"
            : "ready";
}

public sealed record QueryRequest(
    [property: JsonPropertyName("query")] string Query,
    [property: JsonPropertyName("top_k_docs")] int TopKDocs = 5,
    [property: JsonPropertyName("top_k_results")] int TopKResults = 5);

public sealed record QueryResponse
{
    [JsonPropertyName("query")]
    public string Query { get; init; } = "";

    [JsonPropertyName("answer")]
    public string Answer { get; init; } = "";

    [JsonPropertyName("context")]
    public string Context { get; init; } = "";

    [JsonPropertyName("chosen_documents")]
    public IReadOnlyList<DocumentProfile> ChosenDocuments { get; init; } = [];

    [JsonPropertyName("results")]
    public IReadOnlyList<RetrievalResult> Results { get; init; } = [];
}

public sealed record RetrievalResult
{
    [JsonPropertyName("document_id")]
    public string DocumentId { get; init; } = "";

    [JsonPropertyName("content")]
    public string Content { get; init; } = "";

    [JsonPropertyName("source")]
    public string Source { get; init; } = "";

    [JsonPropertyName("score")]
    public double? Score { get; init; }
}

public sealed record UploadStatus(string Filename, string Status, bool IsError = false);
