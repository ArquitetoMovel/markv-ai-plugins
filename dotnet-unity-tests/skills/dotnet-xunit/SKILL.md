---
name: dotnet-xunit
description: >
  Use this skill when the user asks to create, scaffold, review or plan unit tests
  for .NET 8, .NET 9, or .NET 10+ projects, mentions xUnit, FluentAssertions,
  NSubstitute, Testcontainers, or asks about modern .NET test best practices.
  Also activates for: "criar testes", "escrever testes", "testes unitários .NET 8",
  "testes unitários .NET 9", "testes unitários .NET 10", "xUnit", "cobertura de código".
---

# dotnet-xunit — Testes Unitários para .NET 8 / 9 / 10+

> Esta skill cobre projetos com `<TargetFramework>` igual a `net8.0`, `net9.0` ou `net10.0`.
> Para projetos `.NET Framework 4.7.2` use a skill **dotnet-mstest**.

---

## Ponto de entrada canônico

Quando esta skill for acionada automaticamente por palavras-chave do usuário (ex.: "criar testes .NET 8", "escrever testes unitários", "cobrir classe X"), o assistant **deve invocar o agente `dotnet-tester-coordinator`** como ponto de entrada — ele orquestra o fluxo completo `reviewer → planner → creator(s)` e gerencia o diretório de sessão `.dotnet-unity-tests/<session-id>/` na raiz da solução.

Consulte este documento diretamente **apenas** para referência pontual de padrões de código (escrever um `[Fact]` ad-hoc, tirar dúvida de convenção de nomenclatura, lembrar versão de pacote). Para qualquer tarefa end-to-end de planejar + criar testes em uma solução, use o coordinator.

---

## Stack canônica

| Pacote                         | Versão   | Finalidade                          |
|-------------------------------|----------|-------------------------------------|
| `xunit`                       | 2.9.x    | Framework principal                 |
| `xunit.runner.visualstudio`   | 2.8.x    | Integração com VS / Rider / dotnet  |
| `Microsoft.NET.Test.Sdk`      | 17.x     | SDK de execução de testes           |
| `FluentAssertions`            | 6.12.x   | Assertivas legíveis e expressivas   |
| `NSubstitute`                 | 5.1.x    | Mocking sem boilerplate             |
| `Bogus`                       | 35.x     | Geração de dados falsos realistas   |
| `Testcontainers`              | 3.x      | Testes de integração com DB / infra |
| `coverlet.collector`          | 6.x      | Coleta de cobertura de código       |

### `.csproj` mínimo para projeto de testes

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <IsPackable>false</IsPackable>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="xunit" Version="2.9.*" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.8.*">
      <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
      <PrivateAssets>all</PrivateAssets>
    </PackageReference>
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.*" />
    <PackageReference Include="FluentAssertions" Version="6.12.*" />
    <PackageReference Include="NSubstitute" Version="5.1.*" />
    <PackageReference Include="Bogus" Version="35.*" />
    <PackageReference Include="coverlet.collector" Version="6.*">
      <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
      <PrivateAssets>all</PrivateAssets>
    </PackageReference>
  </ItemGroup>

  <ItemGroup>
    <ProjectReference Include="..\<AssemblyUnderTest>\<AssemblyUnderTest>.csproj" />
  </ItemGroup>

</Project>
```

---

## Convenções de nomenclatura

| Elemento        | Padrão                                       | Exemplo                                       |
|----------------|----------------------------------------------|-----------------------------------------------|
| Projeto        | `<Assembly>.Tests.csproj`                    | `OrderService.Tests.csproj`                   |
| Namespace      | `<Assembly>.Tests`                           | `OrderService.Tests`                          |
| Classe         | `<ClassUnderTest>Tests`                      | `OrderProcessorTests`                         |
| Método         | `<Method>_<Scenario>_<ExpectedResult>`       | `Process_ValidOrder_ReturnsConfirmation`       |
| Fixture        | `<ClassUnderTest>Fixture`                    | `DatabaseFixture`                             |

---

## Padrões de teste

### [Fact] — teste simples

```csharp
[Fact]
public void Calculate_PositiveNumbers_ReturnsSum()
{
    // Arrange
    var calculator = new Calculator();

    // Act
    var result = calculator.Calculate(2, 3);

    // Assert
    result.Should().Be(5);
}
```

### [Theory] + [InlineData] — parametrizado com dados inline

```csharp
[Theory]
[InlineData(2, 3, 5)]
[InlineData(-1, 1, 0)]
[InlineData(0, 0, 0)]
public void Calculate_GivenPairs_ReturnsExpectedSum(int a, int b, int expected)
{
    // Arrange
    var calculator = new Calculator();

    // Act
    var result = calculator.Calculate(a, b);

    // Assert
    result.Should().Be(expected);
}
```

### [Theory] + [MemberData] — parametrizado com dados externos

```csharp
public static IEnumerable<object[]> InvalidOrders =>
[
    [null, "Order cannot be null"],
    [new Order { Amount = -1 }, "Amount must be positive"],
];

[Theory]
[MemberData(nameof(InvalidOrders))]
public void Process_InvalidOrder_ThrowsArgumentException(Order order, string reason)
{
    // Arrange
    var processor = new OrderProcessor();

    // Act
    var act = () => processor.Process(order);

    // Assert
    act.Should().Throw<ArgumentException>(reason);
}
```

### Setup/teardown assíncrono com IAsyncLifetime

```csharp
public class OrderRepositoryTests : IAsyncLifetime
{
    private DatabaseConnection _connection = null!;

    public async Task InitializeAsync()
    {
        _connection = await DatabaseConnection.OpenAsync("connection-string");
    }

    public async Task DisposeAsync()
    {
        await _connection.CloseAsync();
    }

    [Fact]
    public async Task Save_ValidOrder_PersistsToDatabase()
    {
        // ...
    }
}
```

### Fixture compartilhada entre testes da mesma classe

```csharp
// Fixture — instanciada uma vez por classe de teste
public class ApiClientFixture : IDisposable
{
    public HttpClient Client { get; } = new HttpClient { BaseAddress = new Uri("https://api.example.com") };
    public void Dispose() => Client.Dispose();
}

// Classe de teste usa IClassFixture<T>
public class ApiClientTests(ApiClientFixture fixture) : IClassFixture<ApiClientFixture>
{
    [Fact]
    public async Task Get_ValidEndpoint_Returns200()
    {
        var response = await fixture.Client.GetAsync("/health");
        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }
}
```

### Log com ITestOutputHelper

```csharp
public class PaymentServiceTests(ITestOutputHelper output)
{
    [Fact]
    public void Process_LargeAmount_LogsAuditEntry()
    {
        output.WriteLine("Testing large payment scenario...");
        // ...
    }
}
```

---

## Workflow de scaffolding

### Phase 1 — Identificar o projeto-alvo
- Glob por `*.csproj` e verificar `<TargetFramework>` → confirmar `net8.0` / `net9.0` / `net10.0`
- Identificar as classes a testar; listar seus métodos públicos e dependências

### Phase 2 — Criar ou localizar o projeto de testes
- Se não existir: `dotnet new xunit -n <Assembly>.Tests -f net8.0`
- Adicionar referência ao projeto principal: `dotnet add reference ../Assembly/Assembly.csproj`
- Adicionar pacotes da stack canônica via `dotnet add package`

### Phase 3 — Estrutura de classes
- Uma classe de teste por classe sob teste
- Agrupar por namespace espelhando a estrutura do projeto principal
- Criar fixtures apenas quando há setup custoso compartilhado entre vários testes

### Phase 4 — Implementar os testes
- Padrão AAA com comentários `// Arrange`, `// Act`, `// Assert`
- Mockar dependências externas com NSubstitute
- Usar Bogus para gerar dados de entrada realistas quando aplicável
- Preferir `FluentAssertions` a `Assert.*` nativo

### Phase 5 — Verificar
```bash
dotnet test --collect:"XPlat Code Coverage"
dotnet test --logger "console;verbosity=detailed"
```

---

## Anti-patterns a evitar

| Anti-pattern                                  | Por quê é problema                                          |
|----------------------------------------------|-------------------------------------------------------------|
| `[SetUp]` / `[TearDown]`                     | São atributos de NUnit/MSTest — não existem no xUnit        |
| Campo ou propriedade estática entre testes   | xUnit cria nova instância por teste; estado não é compartilhado por design |
| Lógica de assert no construtor               | Erros no construtor não são reportados como falhas de teste |
| Herança de classe base com fixtures          | Prefira `IClassFixture<T>` ou `ICollectionFixture<T>`       |
| `Thread.Sleep` em testes assíncronos         | Use `await Task.Delay` ou, melhor, mocks controláveis       |
| `[InlineData]` com objetos complexos         | Use `[MemberData]` ou `[ClassData]` para objetos            |
