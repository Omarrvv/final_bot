export default {
  preset: 'ts-jest/presets/default-esm',
  testEnvironment: 'node',
  extensionsToTreatAsEsm: ['.js'],
  moduleNameMapper: {
    '^(\.{1,2}/.*)\.js$': '$1'
  }
}
