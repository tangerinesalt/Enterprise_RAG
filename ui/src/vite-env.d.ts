/// <reference types="vite/client" />

/* CSS Modules 类型声明 — 让 TypeScript 理解 .module.css 导入 */
declare module '*.module.css' {
  const classes: { readonly [key: string]: string };
  export default classes;
}
