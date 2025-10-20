import { Metadata  } from "next";
import SettingsClient from "./SettingsClient";

export const metadata : Metadata = {
  title: "Settings | Fintrack",
  description: "Manage your Fintrack account settings and preferences.",
}

export default function SettingsPage() {
  return <SettingsClient />;
}
