# Referência — Build e Test via CLI em .NET Framework 4.7.2

> Documento de referência da skill `dotnet-mstest`. Explica como obter, em projetos
> `net472`, a mesma experiência de linha de comando que os agentes têm no .NET moderno
> (`dotnet build` / `dotnet test`), e o que fazer quando isso não é possível.

---

## Resumo executivo

| Operação      | .NET moderno (`net8.0+`) | .NET Framework 4.7.2                                   |
|---------------|--------------------------|-------------------------------------------------------|
| **Build**     | `dotnet build`           | `dotnet build` *se* SDK-style; senão `msbuild`        |
| **Test**      | `dotnet test`            | `dotnet test` *se* projeto de teste SDK-style + MSTest v3 |
| **Run**       | `dotnet run`             | Sem equivalente direto — executa o `.exe` ou hospeda via IIS/IIS Express |
| **Cobertura** | `coverlet` via `dotnet test` | `coverlet` também funciona em `net472` SDK-style  |

**Regra de ouro para os agentes:** sempre que possível, modele o **projeto de testes**
como **SDK-style com `<TargetFramework>net472</TargetFramework>`**. Assim o mesmo
`dotnet build` / `dotnet test` usado no fluxo moderno funciona no legado, sem ferramentas extras.

---

## 1. Caminho preferido — SDK-style + `net472`

Para projetos de teste novos ou migrados, use o `.csproj` SDK-style já recomendado na
seção "Stack canônica" do `SKILL.md`. Com o **.NET SDK** e o **targeting pack do .NET
Framework 4.7.2** instalados no ambiente (local ou CI), os agentes usam os mesmos comandos:

```bash
dotnet build MinhaSolucao.sln
dotnet test MinhaSolucao.sln --logger "console;verbosity=normal"
dotnet build --warnaserror
```

> O `dotnet` CLI **não** é exclusivo do .NET 8+. Ele compila e testa `net472` desde que o
> projeto seja SDK-style e o Developer Pack / targeting pack do 4.7.2 esteja presente.

Este é exatamente o pressuposto do fluxo dos agentes `dotnet-tester-creator`:
`dotnet build` + `dotnet test` para ambos os mundos.

---

## 2. Fallback — projeto legado (formato clássico de `.csproj`)

Muitas aplicações 4.7.2 ainda usam o formato clássico, que não declara `Sdk="..."`:

```xml
<Project ToolsVersion="15.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <Import Project="$(MSBuildExtensionsPath)\$(MSBuildToolsVersion)\Microsoft.Common.props" />
  <!-- ... -->
</Project>
```

Nesses casos `dotnet build` pode falhar ou não ser suportado. O equivalente CLI é **MSBuild**:

```bash
# Windows (Build Tools / Visual Studio)
msbuild MinhaSolucao.sln /t:Build /p:Configuration=Release /v:m

# macOS/Linux — via Mono MSBuild (limitado; muitos projetos FW só compilam de fato no Windows)
msbuild MinhaSolucao.sln /t:Build
```

**Pré-requisito:** Visual Studio Build Tools ou Visual Studio com a workload
**.NET desktop development**. Em CI, o padrão é runner **Windows** com MSBuild do VS
(localizável via `vswhere`).

---

## 3. Testes em projetos 100% legados (sem SDK-style)

Se o projeto de testes ainda é formato antigo com MSTest v1/v2:

| Ferramenta            | Uso                                          |
|-----------------------|----------------------------------------------|
| `vstest.console.exe`  | Runner de testes da plataforma Microsoft     |
| `mstest.exe`          | Legado — evitar                              |

```bash
vstest.console.exe MeuProjeto.Tests\bin\Release\MeuProjeto.Tests.dll
```

**Recomendação para agentes:** migrar **apenas o projeto de testes** para SDK-style +
MSTest v3. É a mudança de menor risco que devolve `dotnet test` (ver guia de migração no `SKILL.md`).

---

## 4. `dotnet run` — por que não há equivalente simples

O .NET Framework não tem o modelo de "projeto executável autocontido" do SDK moderno:

- **Console / WinForms / WPF:** após o build, roda `bin\Release\MeuApp.exe`.
- **ASP.NET (System.Web):** precisa de **IIS**, **IIS Express** ou self-host manual.
- **Windows Service:** instala/inicia via `sc.exe` ou similar.

Para o caso de uso dos agentes o fluxo é **build + test**, não `run`. Validar execução
depende do tipo de app — não existe um único `dotnet run`.

---

## 5. Cobertura de código

Em `net472` **SDK-style**, o `coverlet` funciona como no .NET moderno:

```bash
dotnet test --collect:"XPlat Code Coverage"
```

Em projetos legados sem SDK, as alternativas (OpenCover, Fine Code Coverage, relatórios
do Azure DevOps) são menos amigáveis para automação por agente.

---

## 6. Matriz de detecção (para o `dotnet-tester-reviewer`)

O reviewer já inspeciona `<TargetFramework>` nos `.csproj`. A lógica pode ser estendida
para escolher os comandos certos por projeto:

| Sinal no `.csproj`                          | Comando de build | Comando de test                      |
|---------------------------------------------|------------------|--------------------------------------|
| `Sdk="Microsoft.NET.Sdk"` + `net472`        | `dotnet build`   | `dotnet test`                        |
| Formato clássico (sem atributo `Sdk`)       | `msbuild`        | `vstest.console.exe` ou migrar testes|
| `net8.0+`                                   | `dotnet build`   | `dotnet test` + coverlet             |

---

## 7. Ordem de prioridade recomendada

1. **Garantir .NET SDK + targeting pack 4.7.2** no ambiente do agente (local/CI).
2. **Novos projetos de teste sempre SDK-style** com MSTest v3.
3. **Produção pode continuar legada** — `msbuild` na solution inteira costuma compilar tudo junto.
4. **Documentar no repositório** qual comando usar por projeto (`dotnet` vs `msbuild`), para
   o reviewer detectar via `<Project Sdk=...>` nos `.csproj`.
