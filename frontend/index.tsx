
import React from "react";
import ReactDOM from "react-dom/client";
import { Provider } from "react-redux";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import "../bubble/static/css/main.css"; // tailwind styles
import App from "./App";
import { FeedbackToast, LoadingIndicator } from "./src/components";
import reduxStore from "./src/redux/store";

const rootElement = document.getElementById("root");

if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <Provider store={reduxStore}>
        <LoadingIndicator />
        <App />
        <ToastContainer newestOnTop={true} />
        <FeedbackToast />
      </Provider>
    </React.StrictMode>,
  );
}
