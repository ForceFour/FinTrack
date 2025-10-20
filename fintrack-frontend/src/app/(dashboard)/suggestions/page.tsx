import { Metadata } from "next";
import SuggestionsPage from "./SuggetionClient";

export const metadata : Metadata = {
    title: "Suggestions | Fintrack",
    description: "Personalized financial suggestions powered by AI.",
}

export default function SuggestionsPageWrapper() {
    return <SuggestionsPage />;
}
