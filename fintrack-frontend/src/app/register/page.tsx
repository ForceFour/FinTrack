import { Metadata } from "next";
import RegisterPage from "./RegisterClient";

export const metadata : Metadata = {
  title: "Register | Fintrack",
  description: "Create your Fintrack account and start managing your finances.",
}

export default function RegisterPageWrapper() {
  return <RegisterPage />;
}
