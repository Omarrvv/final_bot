import react from 'eslint-plugin-react';

export default [
  {
    plugins: {
      react
    },
    languageOptions: {
      parserOptions: {
        ecmaFeatures: {
          jsx: true
        }
      }
    },
    rules: {
      'no-unused-vars': 'warn',
      'no-console': 'warn',
      'react/jsx-uses-vars': 'error',
      'react/jsx-uses-react': 'error'
    }
  }
];
