# Contributing to Open Congress Data

Thank you for your interest in contributing to the Open Congress Data project!
This guide will help you get started with contributing data corrections,
updates, and improvements.

## How to Contribute

### Reporting Data Errors

If you find incorrect or outdated information:

1. **Open an Issue**
   - Go to the
     [Issues](https://github.com/bettergovph/open-congress-data/issues) page
   - Click "New Issue"
   - Provide a clear description of the error:
     - Which file contains the error
     - What the incorrect data is
     - What the correct data should be (with sources if possible)
     - Link to official government sources that verify the correction

2. **Include Evidence**
   - Always cite official sources (Senate website, House website, etc.)
   - Include screenshots or links when possible
   - Be specific about dates, names, and numbers

### Submitting Data Corrections

1. **Fork the Repository**
   - Click the "Fork" button on the main repository page
   - Clone your fork locally:
     ```bash
     git clone https://github.com/YOUR-USERNAME/open-congress-data.git
     cd open-congress-data
     ```

2. **Create a Branch**
   - Use a descriptive branch name:
     ```bash
     git checkout -b fix/senator-name-correction
     # or
     git checkout -b update/20th-congress-committees
     ```

3. **Make Your Changes**
   - Edit the relevant TOML files in the `data/` directory
   - Follow the existing data structure and format
   - Ensure all required fields are filled
   - Double-check spelling and formatting

4. **Commit Your Changes**
   - Write clear commit messages:
     ```bash
     git add data/person/01JG7MXZNV8B1234567890ABCD.toml
     git commit -m "fix: correct middle initial for Juan Dela Cruz"
     ```

5. **Submit a Pull Request**
   - Push to your fork: `git push origin your-branch-name`
   - Go to the original repository
   - Click "New Pull Request"
   - Provide a clear description of your changes
   - Reference any related issues

## Data Standards

### File Naming

- Use ULID (Universally Unique Lexicographically Sortable Identifier) for
  filenames
- Generate a ULID at: https://ulidtools.com/ or https://www.ulidgenerator.com/
- Example: `01JG7MXZNV8B1234567890ABCD.toml`
- The ULID should match the entity's `id` field in the TOML file

### Data Verification

Before submitting:

- ✅ Verify data against official government sources
- ✅ Check for typos and formatting errors
- ✅ Ensure consistency with existing data
- ✅ Test that TOML files are valid (no syntax errors)
- ✅ Include source URLs in your pull request description

## Adding New Data

### New Senators or Officials

1. Create a new TOML file in `data/person/`
2. Use a ULID for the filename (e.g., `01JG7MXZNV8B1234567890ABCD.toml`)
3. Include all required fields
4. Add appropriate congress relationships

### New Committees

1. Create a new TOML file in `data/committee/`
2. Use a ULID for the filename (e.g., `01JG7MXZNV8B1234567890ABCD.toml`)
3. Link to appropriate congresses
4. Include all variations of website keys

### New Congress Sessions

1. Create a new TOML file in `data/congress/`
2. Use a ULID for the filename (e.g., `01JG7MXZNV8B1234567890ABCD.toml`)
3. Include accurate date ranges
4. Verify start and end dates

## Code of Conduct

- Be respectful and constructive
- Focus on accuracy and verifiability
- Welcome questions and feedback
- Help others learn and contribute
- Maintain political neutrality - focus on facts

## Getting Help

- Check existing issues for similar problems
- Ask questions in issue discussions
- Tag maintainers for urgent corrections
- Join community discussions

## Recognition

All contributors will be recognized for their efforts. Your contributions help
maintain transparency and accountability in Philippine governance.

## License

By contributing, you agree that your contributions will be dedicated to the
public domain under CC0 1.0 Universal.

---

**Remember**: Every contribution matters! Whether you're fixing a typo, updating
a date, or adding new data, you're helping build a more transparent and
accessible record of Philippine Congress.
