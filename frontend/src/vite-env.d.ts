declare module "*?raw" {
  const content: string;
  export default content;
}

declare module "*?inline" {
  const content: string;
  export default content;
}

// Swagger UI ships no types. Only what the API page calls is declared.
declare module "swagger-ui-dist/swagger-ui-es-bundle.js" {
  interface SwaggerUIInstance {
    specActions: { updateSpec(spec: string): void };
  }
  const SwaggerUI: (options: Record<string, unknown> & { domNode: HTMLElement }) => SwaggerUIInstance;
  export default SwaggerUI;
}
