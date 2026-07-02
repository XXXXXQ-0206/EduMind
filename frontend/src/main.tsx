import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { router } from "@/router";
import "@/styles/globals.css";

const storedTheme = localStorage.getItem("edumind.react.theme");
document.documentElement.classList.toggle("dark", storedTheme !== "light");

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);
