# Contributing to Intric

## TLDR
- **Code Standards**: Follow PEP 8 for Python, project ESLint for frontend, and DDD principles
- **Workflow**: Feature branches, conventional commits, and test coverage requirements
- **Pull Requests**: Clear descriptions, reference issues, and maintain documentation
- **Testing**: Unit tests, integration tests, and API tests with ≥80% coverage
- **Documentation**: Update docs for any feature or API changes

Thank you for your interest in contributing to Intric! This document provides guidelines and instructions for contributing to the project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

Our community is dedicated to providing a harassment-free experience for everyone. We do not tolerate harassment of participants in any form. By participating in this project, you agree to abide by these principles.

## Getting Started

1. **Fork the Repository**:
   - Fork the Intric repository to your GitHub account.
   - Clone your fork locally: `git clone https://github.com/YOUR_USERNAME/intric-community.git`

2. **Set Up Development Environment**:
   - Follow the instructions in the [Development Guide](development-guide.md) to set up your local environment.

3. **Find an Issue**:
   - Look for open issues in our GitHub issue tracker.
   - Comment on the issue to express your interest in working on it.
   - If you have a new idea, open an issue to discuss it before implementing.

## Development Workflow

We follow a branch-based workflow:

1. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
   or
   ```bash
   git checkout -b fix/issue-description
   ```

2. **Commit Your Changes**:
   - We follow conventional commit messages:
     ```
     feat: add new feature X
     fix: resolve issue with Y
     chore: update dependencies
     docs: improve documentation for Z
     test: add tests for feature X
     ```
   - Keep commits focused and atomic.

3. **Stay Up-to-Date**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

## Pull Request Process

1. **Create a Pull Request** from your feature branch to the main Intric repository.

2. **Pull Request Title and Description**:
   - Use a clear, descriptive title.
   - Include a detailed description explaining the changes and their purpose.
   - Reference any related issues using GitHub keywords: "Fixes #123" or "Resolves #456".

3. **Code Review**:
   - All PRs require at least one review from a maintainer.
   - Address all feedback from reviewers.
   - Make requested changes in new commits, then squash them before merging.

4. **CI Checks**:
   - All tests must pass before merging.
   - Code must meet linting standards.
   - Documentation must be updated if applicable.

5. **Merging**:
   - PRs will be merged by a maintainer after approval.
   - We typically use squash merging to keep the history clean.

## Coding Standards

### Python Code
- Follow PEP 8 style guide.
- Use type hints for all function parameters and return values.
- Write docstrings for all public functions, classes, and modules.
- Use Poetry for dependency management.
- Maintain at least 80% test coverage for new code.

### Frontend Code
- Follow the project's ESLint configuration.
- Use SvelteKit conventions for components and routing.
- Use pnpm for package management.
- Maintain responsive and accessible design principles.
- Document component props and events.

### Domain-Driven Design
- Follow the DDD principles outlined in [Domain Driven Design](domain-driven-design.md).
- Ensure new features align with the existing architecture.
- Organize code by business domain, not technical function.
- Use repositories for data access, services for business logic.

## Testing

- Write tests for all new functionality.
- Run existing tests before submitting a PR: `poetry run pytest` for backend, `pnpm run test` for frontend.
- Include both unit and integration tests when appropriate.
- Follow test naming conventions and organize tests by domain.
- Backend tests are located in `tests/` directory, following the domain structure.

## Documentation

- Update documentation for any feature, API, or behavior changes.
- Document all public APIs using appropriate docstrings.
- Follow the existing documentation style.
- Ensure README and relevant guides are updated if applicable.
- Use clear, concise language and include examples where helpful.

## Internationalization (i18n)

The frontend supports multiple languages using Paraglide-JS. When contributing:

### Translation Guidelines

- **Adding UI strings**: Add new strings to both `frontend/apps/web/messages/en.json` and `messages/sv.json`
- **Compile translations**: Always run `pnpm run i18n:compile` after editing translation files
- **Translation keys**: Use descriptive, lowercase keys with underscores (e.g., `"create_assistant": "Create assistant"`)
- **Consistency**: Reuse existing translation keys where possible for UI consistency
- **Testing**: Test your changes in both Swedish and English

### Workflow for Translation Changes

1. **Edit translation files**:
   ```bash
   cd frontend/apps/web
   # Edit messages/en.json and messages/sv.json
   ```

2. **Compile translations**:
   ```bash
   pnpm run i18n:compile
   ```

3. **Check for untranslated strings**:
   ```bash
   node scripts/check-translations.js
   ```

4. **Use in components**:
   ```svelte
   <script>
     import { m } from "$lib/paraglide/messages";
   </script>
   
   <button>{m.your_new_key()}</button>
   ```

### Adding New Languages

If you'd like to add support for a new language, please:

1. Open an issue to discuss the language addition
2. Follow the steps in `frontend/apps/web/LOCALIZATION.md`
3. Ensure proper testing across the new language

For detailed localization documentation, see `frontend/apps/web/LOCALIZATION.md`.

## Community

Join our community to discuss development, ask questions, and get help:

- **Community Forum**: Join by emailing [digitalisering@sundsvall.se](mailto:digitalisering@sundsvall.se)
- **Issue Discussions**: Use GitHub issue discussions for project-specific questions.

Thank you for contributing to Intric! Your efforts help make this project better for everyone.