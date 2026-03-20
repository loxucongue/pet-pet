import App from "./App";
import { createSSRApp } from "vue";

/** 创建 uni-app 应用实例。 */
export function createApp() {
  const app = createSSRApp(App);
  return {
    app,
  };
}
