# 🤖 OpenWebUI Extensions

## 🤝 Project Standards
Read these BEFORE writing any code:
- `.agent/rules/plugin_standards.md`

## 📖 Development Guidelines

### Writing Documentation
- All plugins MUST have both English (`README.md`) and Chinese (`README_CN.md`) documentation
- Follow the template at `docs/PLUGIN_README_TEMPLATE.md`
- Keep versions in sync across all files

### Code Standards
- Use logging instead of print
- Implement Valves for configuration
- Use Lucide icons
- Include i18n support

### Release Process
- Update version numbers in ALL relevant files (code, READMEs, docs)
- Use Conventional Commits format (`feat`, `fix`, `docs`, etc.)
- Create PRs using GitHub CLI (`gh pr create`)

## Author

Fu-Jie  
GitHub: [Fu-Jie/openwebui-extensions](https://github.com/Fu-Jie/openwebui-extensions)

## License

MIT License
