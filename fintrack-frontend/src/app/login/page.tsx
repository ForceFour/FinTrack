import { Metadata } from "next";
import LoginPage from "./LoginClient";

export const metadata : Metadata = {
  title: "Login | Fintrack",
  description: "Access your Fintrack account securely.",
}

export default function LoginPageWrapper() {
  return <LoginPage />;
}
