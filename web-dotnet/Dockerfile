FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build

WORKDIR /src

COPY web-dotnet/MetadataRag.Web.csproj web-dotnet/
RUN dotnet restore web-dotnet/MetadataRag.Web.csproj

COPY web-dotnet/ web-dotnet/
RUN dotnet publish web-dotnet/MetadataRag.Web.csproj \
    --configuration Release \
    --no-restore \
    --output /out

FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime

WORKDIR /app

ENV ASPNETCORE_URLS=http://+:8080 \
    ASPNETCORE_ENVIRONMENT=Production \
    DataProtection__KeyPath=/app/keys

COPY --from=build /out .

RUN mkdir -p /app/keys \
    && chown -R ${APP_UID}:${APP_UID} /app/keys

USER ${APP_UID}

EXPOSE 8080

ENTRYPOINT ["dotnet", "MetadataRag.Web.dll"]
