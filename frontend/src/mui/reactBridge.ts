import { createElement, type ComponentType } from "react";
import { createRoot, type Root } from "react-dom/client";

export function renderReactBridge<Props>(
  host: HTMLElement | null,
  root: Root | null,
  Component: ComponentType<Props>,
  props: Props,
) {
  if (!host) return root;

  const nextRoot = root ?? createRoot(host);
  const BridgeComponent = Component as unknown as ComponentType<Record<string, unknown>>;
  nextRoot.render(createElement(BridgeComponent, props as unknown as Record<string, unknown>));
  return nextRoot;
}

export function unmountReactBridge(root: Root | null) {
  root?.unmount();
}
