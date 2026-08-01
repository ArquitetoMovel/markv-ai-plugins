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

## Canonical entry point

When this skill is automatically activated by user keywords (e.g. "migrate MSTest", "update MSTest", "legacy project tests"), the assistant **must invoke the `dotnet-tester-coordinator` agent** as the entry point — it orchestrates the complete flow `reviewer → planner → creator(s)` and manages the session directory `.dotnet-unity-tests/<session-id>/` at the root of the solution.

Consult this document **only** for reference on specific code patterns (writing a `[TestMethod]` ad-hoc, asking about breaking changes from v2→v3, remembering package versions). For any end-to-end task of planning + creating tests in a solution, use the coordinator.

---

## Strategic decision: when to use MSTest

| Cenário                                  | Framework recomendado       |
|-----------------------------------------|-----------------------------|
| New projects net8,9,10+        | **xUnit.net** (skill `dotnet-xunit`) |
| Maintenance in net472          | **MSTest v3** (this skill)  |
| 100% Microsoft environment (VS + ADO)      | **MSTest v3** (this skill)  |
| Migration from Java/JUnit to modern .NET| NUnit → xUnit               |

---

## Canonical stack for .NET Framework 4.7.2

| Package                    | Version | Purpose                        |
|--------------------------|--------|-----------------------------------|
| `MSTest.TestFramework`   | 3.x    | Framework principal               |
| `MSTest.TestAdapter`     | 3.x    | Runner / integração `dotnet test` |
| `Microsoft.NET.Test.Sdk` | 17.x   | SDK de execução de testes         |

> **Note**: `MSTest.Sdk` (meta-package) **must not** be used in `.NET Framework 4.7.2` projects
> because it requires a complete SDK-style project format. Use the individual packages above.

### Minimum `.csproj` for test project

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

## Build e validação via CLI

Projetos de teste SDK-style com `net472` rodam com os mesmos comandos do .NET moderno
(`dotnet build` / `dotnet test`). Para projetos legados (formato clássico de `.csproj`),
o equivalente é `msbuild` + `vstest.console.exe`.

> Recomendações completas de build/test/cobertura por tipo de projeto, fallback para MSBuild
> e matriz de detecção para o reviewer: ver [build-cli-reference.md](build-cli-reference.md).

---

## Convenções de nomenclatura

| Elemento   | Padrão                                 | Exemplo                                  |
|-----------|----------------------------------------|------------------------------------------|
| Projeto   | `<Assembly>.Tests.csproj`              | `OrderService.Tests.csproj`              |
| Namespace | `<Assembly>.Tests`                     | `OrderService.Tests`                     |
| Classe    | `[TestClass] <ClassUnderTest>Tests`    | `OrderProcessorTests`                    |
| Método    | `[TestMethod] <Method>_<Scenario>_<ExpectedResult>` | `Process_ValidOrder_ReturnsConfirmation` |

---

## MSTest v3 test patterns

### Simple test with [TestMethod]

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

### Parameterized with [DataRow] + [DataTestMethod]

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

### Parameterized with [DynamicData] — complex data

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

### Class fixture with [ClassInitialize] and [ClassCleanup]

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

### Global fixture with [AssemblyInitialize] and [AssemblyCleanup]

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

### Setup and teardown by method with [TestInitialize] and [TestCleanup]

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

### Parallelism (MSTest v3 only)

```csharp
// Em AssemblyInfo.cs ou no arquivo de setup da assembly
[assembly: Parallelize(Workers = 0, Scope = ExecutionScope.MethodLevel)]
```

> `Workers = 0` usa o número de CPUs disponíveis.
> `Scope = ExecutionScope.ClassLevel` paraleliza por classe; `MethodLevel` por método.

---

## MSTest v2 → MSTest v3 migration guide

### Phase 1 — Diagnosis

Find all test projects with MSTest:

```bash
# Find projects with reference to MSTest
grep -rl "MSTest.TestFramework" --include="*.csproj" .

# Check current package versions
grep -A1 "MSTest" **/*.csproj
```

Using the Claude tools:
- Glob `**/*.csproj` and Grep for `MSTest.TestFramework`
- Check current version (`2.x` confirms it is v2)
- List all `[ClassInitialize]` without `TestContext` parameter (breaking change)
- List all `[DataRow]` in methods without `[DataTestMethod]` (breaking change)

### Phase 2 — Update packages

Update each affected `.csproj`:

```xml
<!-- DE (MSTest v2) -->
<PackageReference Include="MSTest.TestFramework" Version="2.*" />
<PackageReference Include="MSTest.TestAdapter" Version="2.*" />

<!-- PARA (MSTest v3) -->
<PackageReference Include="MSTest.TestFramework" Version="3.*" />
<PackageReference Include="MSTest.TestAdapter" Version="3.*" />
```

Run restore to validate:
```bash
dotnet restore
```

### Phase 3 — Fix breaking changes

| Change | v2 behavior | v3 behavior | Required action |
|---------|-----------------|-----------------|-----------------|
| `[DataRow]` without `[DataTestMethod]` | Ignored silently | Compilation error | Replace `[TestMethod]` with `[DataTestMethod]` |
| `[ClassInitialize]` without `TestContext` | Allowed | Required | Add `TestContext context` as parameter |
| `Assert.ThrowsException` async | Limited / workaround | `Assert.ThrowsExceptionAsync<T>` | Migrate to async version |
| Nullable annotations | Not supported | Fully annotated | Review nullable warnings |

**Fix `[ClassInitialize]` without TestContext:**

```csharp
// v2 — allowed but not recommended
[ClassInitialize]
public static void ClassInit() { }

// v3 — TestContext parameter is required
[ClassInitialize]
public static void ClassInit(TestContext context) { }
```

**Fix `[DataRow]` in `[TestMethod]`:**

```csharp
// v2 — [DataRow] with [TestMethod] was ignored silently
[TestMethod]
[DataRow(1, 2)]
public void Add_TwoNumbers_ReturnsSum(int a, int b) { }

// v3 — must use [DataTestMethod]
[DataTestMethod]
[DataRow(1, 2)]
public void Add_TwoNumbers_ReturnsSum(int a, int b) { }
```

**Migrate `Assert.ThrowsException` async:**

```csharp
// v2 — common workaround
Assert.ThrowsException<Exception>(() => asyncMethod().GetAwaiter().GetResult());

// v3 — correct way
await Assert.ThrowsExceptionAsync<Exception>(() => asyncMethod());
```

### Phase 4 — Habilitar paralelismo (opcional)

Create or update `AssemblyInfo.cs` in the test project:

```csharp
using Microsoft.VisualStudio.TestTools.UnitTesting;

[assembly: Parallelize(Workers = 0, Scope = ExecutionScope.MethodLevel)]
```

Identify tests with shared state that **should not** run in parallel:

```csharp
[TestClass]
[DoNotParallelize]  // Protects entire class
public class StatefulIntegrationTests { }

// Or by individual method:
[TestMethod]
[DoNotParallelize]
public void Test_WithSharedResource() { }
```

### Phase 5 — Final validation

```bash
# Run all tests
dotnet test --logger "console;verbosity=normal"

# Check for obsolete warnings
dotnet build --warnaserror

# Compare test count (should be equal before and after)
dotnet test --logger "trx;LogFileName=results.trx"
```

Validation checklist:
- [ ] Test count equal or greater than before migration
- [ ] Zero build errors
- [ ] Zero warnings of `[Obsolete]` related to MSTest
- [ ] Parameterized tests executing all data cases
- [ ] Class and assembly fixtures initializing/cleaning correctly

---

## Anti-patterns to avoid

| Anti-pattern                                    | Why is it a problem                                          |
|------------------------------------------------|-------------------------------------------------------------|
| `[Theory]` / `[InlineData]`                    | São atributos do xUnit — não existem no MSTest              |
| `[SetUp]` / `[TearDown]`                       | São atributos do NUnit — use `[TestInitialize]` / `[TestCleanup]` |
| `MSTest.Sdk` in .NET Framework 4.7.2 projects  | Meta-package requires SDK-style project; incompatible with FW   |
| `[DataRow]` with `[TestMethod]` (v3)            | Compilation error; use `[DataTestMethod]`             |
| Inheritance between classes `[TestClass]`            | MSTest does not support reliable inheritance of test attributes |
| Static mutable state in parallel tests    | Race conditions; use `[DoNotParallelize]` where necessary   |
