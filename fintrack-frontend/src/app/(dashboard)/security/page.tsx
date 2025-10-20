import { Metadata } from "next";
import SecurityPage from "./SecurityClient";

export const metadata : Metadata = {
  title: "Security | Fintrack",
  description: "Your financial security powered by AI.",
}

export default function SecurityPageWrapper() {
  return <SecurityPage />;
}
