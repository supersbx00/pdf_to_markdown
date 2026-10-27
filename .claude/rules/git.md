# Reglas de Git

## 1. Ramas
- `main`: producción.
- `dev`: integración.
- `feature/<nombre>`: funcionalidad nueva (ej. `feature/logs-dagster`).
- `fix/<nombre>`: corrección de un error (ej. `fix/estado-assets`).
- `release/<nombre>`: preparación de una versión.
- `refactor/<nombre>`: reestructurar código sin cambiar su comportamiento.
- `chore/<nombre>`: mantenimiento (dependencias, configuración, tooling).
- `test/<nombre>`: agregar o corregir pruebas unitarias o de integración.
- `<nombre>` en minúsculas y kebab-case (`palabras-separadas-por-guion`), sin tildes ni espacios.

- Todas las ramas salen de `dev` y vuelven a `dev`, excepto `release/<nombre>`, que sale de `dev` y va hacia `main`.
- **Prohibido trabajar directo en `main` o `dev`.** Si Claude está en una de ellas, primero crea la rama que corresponda.

**Antes de crear una rama**, Claude pregunta al programador qué tipo es (`feature`, `fix`, `release`, `refactor`, `chore` o `test`) y el nombre. Si es `test`, pregunta también si serán pruebas unitarias, de integración o ambas. Si el programador ya lo indicó, no se vuelve a preguntar. En un feature nuevo, esta pregunta va dentro del protocolo de preguntas de `CLAUDE.md`.

## 2. Commits
- Claude solo commitea cuando el usuario lo pide.
- Formato **Conventional Commits en español**: `<tipo>(<feature>): <descripción en minúscula, sin punto final>`.
  - Tipos: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`.
  - Scope: el feature afectado (`assets`, `grupos`, `jobs`...); si son varios, separados por coma: `refactor(assets,grupos): ...`.
  - Ejemplo: `fix(grupos): bajar a 15 s el cache de ultimas materializaciones`.
- **No** agregar `Co-Authored-By` ni ninguna otra atribución a Claude en los commits ni en los PR.

## 3. Push
- Claude **nunca** hace `git push`. El push lo hace siempre el usuario.

## 4. Comandos destructivos
- Nada de `git reset --hard`, `git push --force`, `git rebase`, `git branch -D`, `git clean -f` ni `git checkout -- <archivo>` sin confirmación explícita del usuario.
