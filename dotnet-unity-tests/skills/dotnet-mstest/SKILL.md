---
name: dotnet-mstest
description: >
  Use this skill when the user is working with .NET Framework 4.7.2 test projects,
  mentions MSTest, asks to create MSTest tests, or requests migration from MSTest v2
  to MSTest v3. Also activates for keywords: "legado", "legacy .NET", "framework 4.7",
  "migrate MSTest", "atualizar MSTest", "MSTest v3", "projeto legado", "testes framework".
---

# dotnet-mstest — Testes Unitários para .NET Framework 4.7.2

> Esta skill cobre projetos com `<TargetFramework>` igual a `net472` (`.NET Framework 4.7.2`).
> Para projetos `.NET 8 / 9 / 10+` use a skill **dotnet-xunit**.

---

## Ponto de entrada canônico

Quando esta skill for acionada automaticamente por palavras-chave do usuário (ex.: "migrar MSTest", "atualizar MSTest", "testes projeto legado"), o assistant **deve invocar o agente `dotnet-tester-coordinator`** como ponto de entrada — ele orquestra o fluxo completo `reviewer → planner → creator(s)` e gerencia o diretório de sessão `.dotnet-unity-tests/<session-id>/` na raiz da solução.

Consulte este documento diretamente **apenas** para referência pontual de padrões de código (escrever um `[TestMethod]` ad-hoc, tirar dúvida sobre breaking change v2→v3, lembrar versão de pacote). Para qualquer tarefa end-to-end de planejar + criar testes em uma solução, use o coordinator.

---

## Decisão estratégica: quando usar MSTest

| Cenário                                  | Framework recomendado       |
|-----------------------------------------|-----------------------------|
| Projeto novo em .NET 8 / 9 / 10+        | **xUnit.net** (skill `dotnet-xunit`) |
| Manutenção em .NET Framework 4.7.2      | **MSTest v3** (esta skill)  |
| Ambiente 100% Microsoft (VS + ADO)      | **MSTest v3** (esta skill)  |
| Migração de Java/JUnit para .NET moderno| NUnit → xUnit               |

---

## Stack canônica para .NET Framework 4.7.2

| Pacote                    | Versão | Finalidade                        |
|--------------------------|--------|-----------------------------------|
| `MSTest.TestFramework`   | 3.x    | Framework principal               |
| `MSTest.TestAdapter`     | 3.x    | Runner / integração `dotnet test` |
| `Microsoft.NET.Test.Sdk` | 17.x   | SDK de execução de testes         |

> **Nota**: `MSTest.Sdk` (meta-package) **não** deve ser usado em projetos `.NET Framework 4.7.2`
> pois exige SDK-style project format completo. Use os pacotes individuais acima.

### `.csproj` mínimo para projeto de testes

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>net472</TargetFramework>
    <IsPackable>false</IsPackable>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="MSTest.TestFramework" Version="3.*" />
    <PackageReference Include="MSTest.TestAdapter" Version="3.*" />
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.*" />
  </ItemGroup>

  <ItemGroup>
    <ProjectReference Include="..\<AssemblyUnderTest>\<AssemblyUnderTest>.csproj" />
  </ItemGroup>

</Project>
```

---

## Convenções de nomenclatura

| Elemento   | Padrão                                 | Exemplo                                  |
|-----------|----------------------------------------|------------------------------------------|
| Projeto   | `<Assembly>.Tests.csproj`              | `OrderService.Tests.csproj`              |
| Namespace | `<Assembly>.Tests`                     | `OrderService.Tests`                     |
| Classe    | `[TestClass] <ClassUnderTest>Tests`    | `OrderProcessorTests`                    |
| Método    | `[TestMethod] <Method>_<Scenario>_<ExpectedResult>` | `Process_ValidOrder_ReturnsConfirmation` |

---

## Padrões de teste MSTest v3

### Teste simples com [TestMethod]

```csharp
[TestClass]
public class CalculatorTests
{
    [TestMethod]
    public void Calculate_PositiveNumbers_ReturnsSum()
    {
        // Arrange
        var calculator = new Calculator();

        // Act
        var result = calculator.Calculate(2, 3);

        // Assert
        Assert.AreEqual(5, result);
    }
}
```

### Parametrizado com [DataRow] + [DataTestMethod]

```csharp
[TestClass]
public class CalculatorTests
{
    [DataTestMethod]
    [DataRow(2, 3, 5)]
    [DataRow(-1, 1, 0)]
    [DataRow(0, 0, 0)]
    public void Calculate_GivenPairs_ReturnsExpectedSum(int a, int b, int expected)
    {
        // Arrange
        var calculator = new Calculator();

        // Act
        var result = calculator.Calculate(a, b);

        // Assert
        Assert.AreEqual(expected, result);
    }
}
```

### Parametrizado com [DynamicData] — dados complexos

```csharp
[TestClass]
public class OrderProcessorTests
{
    public static IEnumerable<object[]> InvalidOrders
    {
        get
        {
            yield return new object[] { null, "Order cannot be null" };
            yield return new object[] { new Order { Amount = -1 }, "Amount must be positive" };
        }
    }

    [DataTestMethod]
    [DynamicData(nameof(InvalidOrders))]
    public void Process_InvalidOrder_ThrowsArgumentException(Order order, string reason)
    {
        // Arrange
        var processor = new OrderProcessor();

        // Act & Assert
        Assert.ThrowsException<ArgumentException>(() => processor.Process(order), reason);
    }
}
```

### Fixture de classe com [ClassInitialize] e [ClassCleanup]

```csharp
[TestClass]
public class DatabaseTests
{
    private static DatabaseConnection _connection;

    [ClassInitialize]
    public static void ClassInit(TestContext context)  // TestContext é obrigatório no v3
    {
        _connection = DatabaseConnection.Open("connection-string");
    }

    [ClassCleanup]
    public static void ClassCleanup()
    {
        _connection?.Close();
    }

    [TestMethod]
    public void Query_ValidSql_ReturnsResults()
    {
        var results = _connection.Query("SELECT 1");
        Assert.IsNotNull(results);
    }
}
```

### Fixture global com [AssemblyInitialize] e [AssemblyCleanup]

```csharp
[TestClass]
public class TestAssemblySetup
{
    [AssemblyInitialize]
    public static void AssemblyInit(TestContext context)
    {
        // Executado uma vez antes de todos os testes da assembly
    }

    [AssemblyCleanup]
    public static void AssemblyCleanup()
    {
        // Executado uma vez após todos os testes da assembly
    }
}
```

### Setup e teardown por método com [TestInitialize] e [TestCleanup]

```csharp
[TestClass]
public class PaymentServiceTests
{
    private PaymentService _service;

    [TestInitialize]
    public void TestInit()
    {
        _service = new PaymentService();
    }

    [TestCleanup]
    public void TestCleanup()
    {
        _service?.Dispose();
    }

    [TestMethod]
    public void Process_ValidPayment_ReturnsReceipt()
    {
        var receipt = _service.Process(new Payment { Amount = 100 });
        Assert.IsNotNull(receipt);
    }
}
```

### Paralelismo (MSTest v3 apenas)

```csharp
// Em AssemblyInfo.cs ou no arquivo de setup da assembly
[assembly: Parallelize(Workers = 0, Scope = ExecutionScope.MethodLevel)]
```

> `Workers = 0` usa o número de CPUs disponíveis.
> `Scope = ExecutionScope.ClassLevel` paraleliza por classe; `MethodLevel` por método.

---

## Guia de migração MSTest v2 → MSTest v3

### Phase 1 — Diagnóstico

Localizar todos os projetos de teste com MSTest:

```bash
# Encontrar projetos com referência ao MSTest
grep -rl "MSTest.TestFramework" --include="*.csproj" .

# Ver versão atual dos pacotes
grep -A1 "MSTest" **/*.csproj
```

Usando as ferramentas do Claude:
- Glob `**/*.csproj` e Grep por `MSTest.TestFramework`
- Identificar a versão atual (`2.x` confirma que é v2)
- Listar todos os `[ClassInitialize]` sem parâmetro `TestContext` (breaking change)
- Listar todos os `[DataRow]` em métodos sem `[DataTestMethod]` (breaking change)

### Phase 2 — Atualização de pacotes

Atualizar cada `.csproj` afetado:

```xml
<!-- DE (MSTest v2) -->
<PackageReference Include="MSTest.TestFramework" Version="2.*" />
<PackageReference Include="MSTest.TestAdapter" Version="2.*" />

<!-- PARA (MSTest v3) -->
<PackageReference Include="MSTest.TestFramework" Version="3.*" />
<PackageReference Include="MSTest.TestAdapter" Version="3.*" />
```

Executar restore para validar:
```bash
dotnet restore
```

### Phase 3 — Corrigir breaking changes

| Mudança | Comportamento v2 | Comportamento v3 | Ação necessária |
|---------|-----------------|-----------------|-----------------|
| `[DataRow]` sem `[DataTestMethod]` | Ignorado silenciosamente | Erro de compilação | Trocar `[TestMethod]` por `[DataTestMethod]` |
| `[ClassInitialize]` sem `TestContext` | Permitido | Obrigatório | Adicionar `TestContext context` como parâmetro |
| `Assert.ThrowsException` assíncrono | Limitado / workaround | `Assert.ThrowsExceptionAsync<T>` | Migrar para versão async |
| Nullable annotations | Sem suporte | Totalmente anotado | Revisar warnings nullable |

**Corrigir [ClassInitialize] sem TestContext:**

```csharp
// v2 — permitido mas não recomendado
[ClassInitialize]
public static void ClassInit() { }

// v3 — parâmetro TestContext obrigatório
[ClassInitialize]
public static void ClassInit(TestContext context) { }
```

**Corrigir [DataRow] em [TestMethod]:**

```csharp
// v2 — [DataRow] com [TestMethod] era ignorado silenciosamente
[TestMethod]
[DataRow(1, 2)]
public void Add_TwoNumbers_ReturnsSum(int a, int b) { }

// v3 — deve usar [DataTestMethod]
[DataTestMethod]
[DataRow(1, 2)]
public void Add_TwoNumbers_ReturnsSum(int a, int b) { }
```

**Migrar Assert.ThrowsException assíncrono:**

```csharp
// v2 — workaround comum
Assert.ThrowsException<Exception>(() => asyncMethod().GetAwaiter().GetResult());

// v3 — forma correta
await Assert.ThrowsExceptionAsync<Exception>(() => asyncMethod());
```

### Phase 4 — Habilitar paralelismo (opcional)

Criar ou atualizar `AssemblyInfo.cs` no projeto de testes:

```csharp
using Microsoft.VisualStudio.TestTools.UnitTesting;

[assembly: Parallelize(Workers = 0, Scope = ExecutionScope.MethodLevel)]
```

Identificar testes com estado compartilhado que **não devem** rodar em paralelo:

```csharp
[TestClass]
[DoNotParallelize]  // Protege classe inteira
public class StatefulIntegrationTests { }

// Ou por método individual:
[TestMethod]
[DoNotParallelize]
public void Test_WithSharedResource() { }
```

### Phase 5 — Verificação final

```bash
# Executar todos os testes
dotnet test --logger "console;verbosity=normal"

# Verificar sem warnings de obsolescência
dotnet build --warnaserror

# Comparar contagem de testes (deve ser igual antes e depois)
dotnet test --logger "trx;LogFileName=results.trx"
```

Checklist de validação:
- [ ] Contagem de testes igual ou maior que antes da migração
- [ ] Zero erros de build
- [ ] Zero warnings de `[Obsolete]` relacionados ao MSTest
- [ ] Testes parametrizados executando todos os casos de dados
- [ ] Fixtures de classe e assembly inicializando/limpando corretamente

---

## Anti-patterns a evitar

| Anti-pattern                                    | Por quê é problema                                          |
|------------------------------------------------|-------------------------------------------------------------|
| `[Theory]` / `[InlineData]`                    | São atributos do xUnit — não existem no MSTest              |
| `[SetUp]` / `[TearDown]`                       | São atributos do NUnit — use `[TestInitialize]` / `[TestCleanup]` |
| `MSTest.Sdk` em projetos .NET Framework 4.7.2  | Meta-package exige SDK-style project; incompatível com FW   |
| `[DataRow]` com `[TestMethod]` (v3)            | Gera erro de compilação; use `[DataTestMethod]`             |
| Herança entre classes `[TestClass]`            | MSTest não suporta herança de atributos de teste de forma confiável |
| Estado estático mutável em testes paralelos    | Race conditions; use `[DoNotParallelize]` onde necessário   |
