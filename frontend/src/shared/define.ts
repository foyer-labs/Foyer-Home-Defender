// Define custom elements once Home Assistant's element registry is the final one.
//
// When its app starts, the Home Assistant frontend replaces the custom element
// registry with its own (the scoped custom element registry polyfill). The card is
// loaded as an extra module on every page and can run before that: an element
// defined in the old registry is unknown to the new one, so the card is listed in
// the "add card" picker but cannot be created, and cannot be added from the UI
// (decision 167). So every definition waits until the app has defined
// <home-assistant>. Outside Home Assistant (the screenshot harness) there is nothing
// to wait for.
const ready: Promise<unknown> =
  document.querySelector("home-assistant") && !customElements.get("home-assistant")
    ? customElements.whenDefined("home-assistant")
    : Promise.resolve();

/** Runs `action` once the element registry is Home Assistant's final one. */
export const whenReady = (action: () => void): void => void ready.then(action);

/** Defines an element, once, in the final registry. */
export function define(name: string, element: CustomElementConstructor): void {
  whenReady(() => {
    if (!customElements.get(name)) customElements.define(name, element);
  });
}
