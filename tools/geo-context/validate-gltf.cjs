// Khronos glTF validator for asset delivery; no browser or frontend execution.
const fs = require('node:fs/promises')
const path = require('node:path')
const validator = require('gltf-validator')

async function main() {
  const directory = path.resolve(process.argv[2])
  const files = (await fs.readdir(path.join(directory, 'tiles'))).filter((file) => file.endsWith('.glb'))
  const reports = []
  for (const file of files) {
    const source = path.join(directory, 'tiles', file)
    const report = await validator.validateBytes(new Uint8Array(await fs.readFile(source)), {
      uri: source,
      maxIssues: 30,
      externalResourceFunction: async (uri) => new Uint8Array(await fs.readFile(path.resolve(path.dirname(source), uri))),
    })
    reports.push({ file, errors: report.issues.numErrors, warnings: report.issues.numWarnings, messages: report.issues.messages })
  }
  const result = { errors: reports.reduce((n, r) => n + r.errors, 0), warnings: reports.reduce((n, r) => n + r.warnings, 0), files: reports.length, reports }
  await fs.writeFile(path.join(directory, 'gltf-validation.json'), JSON.stringify(result, null, 2) + '\n')
  console.log(JSON.stringify({ files: result.files, errors: result.errors, warnings: result.warnings }))
  if (result.errors || result.warnings) process.exitCode = 1
}
main().catch((error) => { console.error(error); process.exitCode = 1 })
