import { Metadata } from "next";
import UploadPage from "./UploadClient";

export const metadata : Metadata = {
  title: "Upload | Fintrack",
  description: "Upload your financial data securely powered by AI.",
}

export default function UploadPageWrapper() {
  return <UploadPage />;
}

