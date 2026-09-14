import { css } from "lit";

// Colours come from the Home Assistant theme, so both light and dark themes work.
export const stateStyles = css`
  .state {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 500;
    background: var(--secondary-background-color);
    color: var(--primary-text-color);
  }
  .state::before {
    content: "";
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
  }
  .state.disarmed,
  .state.closed {
    color: var(--success-color, #2e9e4f);
  }
  .state.armed {
    color: var(--info-color, #0277bd);
  }
  .state.triggered,
  .state.fault {
    color: var(--error-color, #d32f2f);
  }
  .state.open {
    color: var(--warning-color, #c77700);
  }
`;
