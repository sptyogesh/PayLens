import { redirect } from "next/navigation";

import { ROUTES } from "@/lib/constants";

/** The dashboard arrives with 002; until then the home page is the transactions list. */
export default function Home() {
  redirect(ROUTES.transactions);
}
