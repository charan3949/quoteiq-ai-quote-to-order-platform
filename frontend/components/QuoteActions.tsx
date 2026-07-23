"use client";

import * as XLSX from "xlsx";
import type { Quote } from "../types/quote";
const CUSTOMER_EMAILS: Record<string, string> = {
  "CUST-1001": "buyer@abcconstruction.com",
  "CUST-1002": "purchasing@desertridgebuilders.com",
  "CUST-1004": "orders@sunvalleyframing.com",
};

type QuoteActionsProps = {
  quote: Quote;
  token: string;
  apiUrl: string;
  userEmail: string;
  onQuoteUpdated: (quote: Quote) => void;
  onMessage: (message: string) => void;
  onLoading: (loading: boolean) => void;
};

export default function QuoteActions({
  quote,
  token,
  apiUrl,
  userEmail,
  onQuoteUpdated,
  onMessage,
  onLoading,
}: QuoteActionsProps) {
  async function readResponse(response: Response) {
    const contentType = response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
      return response.json();
    }

    return response.text();
  }

  async function refreshQuote() {
    const response = await fetch(
      `${apiUrl}/quotes/${quote.quote_id}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    const data = await readResponse(response);

    if (!response.ok) {
      throw new Error(
        typeof data === "object" && data?.detail
          ? data.detail
          : "Unable to refresh quote"
      );
    }

    onQuoteUpdated(data as Quote);
  }

  async function approveQuote() {
    const confirmed = window.confirm(
      `Approve quote ${quote.quote_id}?`
    );

    if (!confirmed) {
      return;
    }

    onLoading(true);
    onMessage("");

    try {
      const response = await fetch(
        `${apiUrl}/quotes/${quote.quote_id}/approve`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            reviewed_by: userEmail,
          }),
        }
      );

      const data = await readResponse(response);

      if (!response.ok) {
        throw new Error(
          typeof data === "object" && data?.detail
            ? data.detail
            : "Quote approval failed"
        );
      }

      await refreshQuote();
      onMessage("Quote approved successfully.");
    } catch (error) {
      onMessage(
        error instanceof Error
          ? error.message
          : "Quote approval failed"
      );
    } finally {
      onLoading(false);
    }
  }

  async function rejectQuote() {
    const reason = window.prompt(
      "Enter the reason for rejecting this quote:"
    );

    if (!reason?.trim()) {
      return;
    }

    onLoading(true);
    onMessage("");

    try {
      const response = await fetch(
        `${apiUrl}/quotes/${quote.quote_id}/reject`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            reviewed_by: userEmail,
            reason: reason.trim(),
          }),
        }
      );

      const data = await readResponse(response);

      if (!response.ok) {
        throw new Error(
          typeof data === "object" && data?.detail
            ? data.detail
            : "Quote rejection failed"
        );
      }

      await refreshQuote();
      onMessage("Quote rejected successfully.");
    } catch (error) {
      onMessage(
        error instanceof Error
          ? error.message
          : "Quote rejection failed"
      );
    } finally {
      onLoading(false);
    }
  }

  async function downloadPdf() {
    onLoading(true);
    onMessage("");

    try {
      const response = await fetch(
        `${apiUrl}/quotes/${quote.quote_id}/pdf`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        const data = await readResponse(response);

        throw new Error(
          typeof data === "object" && data?.detail
            ? data.detail
            : "PDF download failed"
        );
      }

      const blob = await response.blob();
      const downloadUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = downloadUrl;
      link.download = `${quote.quote_id}.pdf`;

      document.body.appendChild(link);
      link.click();
      link.remove();

      URL.revokeObjectURL(downloadUrl);

      onMessage("Quote PDF downloaded successfully.");
    } catch (error) {
      onMessage(
        error instanceof Error
          ? error.message
          : "PDF download failed"
      );
    } finally {
      onLoading(false);
    }
  }

  function exportExcel() {
    if (!quote.priced_lines?.length) {
      onMessage("There are no quote lines to export.");
      return;
    }

    const worksheetRows = quote.priced_lines.map((line) => ({
      "Quote ID": quote.quote_id,
      Customer: quote.customer_name,
      "Customer ID": quote.customer_id,
      SKU: line.sku,
      Product: line.product_name,
      Category: line.category,
      Quantity: line.quantity,
      UOM: line.uom_raw || "",
      "Base Cost": line.base_cost,
      "List Price": line.list_price,
      "Unit Price": line.unit_price,
      "Line Total": line.line_total,
      "Margin %": line.margin_pct,
      "Pricing Rule": line.pricing_rule_applied,
      "Risk Flag": line.risk_flag ? "Yes" : "No",
      "Risk Reason": line.risk_reason || "",
      Status: quote.quote_status,
    }));

    const worksheet = XLSX.utils.json_to_sheet(worksheetRows);

    worksheet["!cols"] = [
      { wch: 18 },
      { wch: 24 },
      { wch: 14 },
      { wch: 20 },
      { wch: 32 },
      { wch: 18 },
      { wch: 12 },
      { wch: 10 },
      { wch: 12 },
      { wch: 12 },
      { wch: 12 },
      { wch: 14 },
      { wch: 12 },
      { wch: 24 },
      { wch: 12 },
      { wch: 30 },
      { wch: 22 },
    ];

    const summaryRows = [
      ["Quote ID", quote.quote_id],
      ["Customer", quote.customer_name],
      ["Customer ID", quote.customer_id],
      ["Price Class", quote.price_class],
      ["Quote Status", quote.quote_status],
      ["Quote Subtotal", quote.quote_subtotal],
      ["Estimated Margin %", quote.estimated_margin_pct],
      ["Risk Count", quote.risk_count],
      ["Confidence %", quote.quote_confidence],
    ];

    const summaryWorksheet =
      XLSX.utils.aoa_to_sheet(summaryRows);

    summaryWorksheet["!cols"] = [
      { wch: 24 },
      { wch: 30 },
    ];

    const workbook = XLSX.utils.book_new();

    XLSX.utils.book_append_sheet(
      workbook,
      summaryWorksheet,
      "Quote Summary"
    );

    XLSX.utils.book_append_sheet(
      workbook,
      worksheet,
      "Line Items"
    );

    XLSX.writeFile(
      workbook,
      `${quote.quote_id}-quote.xlsx`
    );

    onMessage("Excel quote exported successfully.");
  }

  async function createOrder() {
    const confirmed = window.confirm(
      `Create an ERP sales order from ${quote.quote_id}?`
    );

    if (!confirmed) {
      return;
    }

    onLoading(true);
    onMessage("");

    try {
      const response = await fetch(
        `${apiUrl}/quotes/${quote.quote_id}/create-order`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await readResponse(response);

      if (!response.ok) {
        throw new Error(
          typeof data === "object" && data?.detail
            ? data.detail
            : "Sales order creation failed"
        );
      }

      await refreshQuote();

      const orderId =
        typeof data === "object"
          ? data?.sales_order?.sales_order_id
          : null;

      onMessage(
        orderId
          ? `ERP sales order ${orderId} created successfully.`
          : "ERP sales order created successfully."
      );
    } catch (error) {
      onMessage(
        error instanceof Error
          ? error.message
          : "Sales order creation failed"
      );
    } finally {
      onLoading(false);
    }
  }

  function emailCustomer() {
  const customerEmails: Record<string, string> = {
    "CUST-1001": "buyer@abcconstruction.com",
    "CUST-1002": "purchasing@desertridgebuilders.com",
    "CUST-1004": "orders@sunvalleyframing.com",
  };

  const customerEmail =
    customerEmails[quote.customer_id] || "";

  const subject = encodeURIComponent(
    `Quote ${quote.quote_id} from QuoteIQ`
  );

  const body = encodeURIComponent(
    [
      `Hello ${quote.customer_name},`,
      "",
      `Your quotation ${quote.quote_id} is ready.`,
      "",
      `Quote value: $${quote.quote_subtotal.toFixed(2)}`,
      `Estimated margin: ${quote.estimated_margin_pct.toFixed(2)}%`,
      `Status: ${quote.quote_status}`,
      "",
      "Please contact our sales team if you have any questions.",
      "",
      "Thank you.",
    ].join("\n")
  );

  window.location.href =
    `mailto:${customerEmail}?subject=${subject}&body=${body}`;

  onMessage(
    customerEmail
      ? `Email draft opened for ${customerEmail}.`
      : "Email draft opened. No customer email was found."
  );
}

  const isApproved =
    quote.quote_status === "APPROVED" ||
    quote.quote_status === "CONVERTED_TO_ORDER";

  const isRejected = quote.quote_status === "REJECTED";

  return (
    <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-3 border-b border-slate-200 pb-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="text-lg font-bold text-slate-950">
            Quote actions
          </h3>

          <p className="mt-1 text-sm text-slate-500">
            Review, approve, export and convert this quote.
          </p>
        </div>

        <span className="w-fit rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
          {quote.quote_status}
        </span>
      </div>

      {quote.pricing_status_message && (
        <div className="mt-4 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
          <span className="font-semibold">Pricing incomplete: </span>
          {quote.pricing_status_message}
        </div>
      )}

      <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <button
          type="button"
          onClick={approveQuote}
          disabled={isApproved || isRejected}
          className="rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Approve Quote
        </button>

        <button
          type="button"
          onClick={rejectQuote}
          disabled={isApproved || isRejected}
          className="rounded-xl bg-red-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Reject Quote
        </button>

        <button
          type="button"
          onClick={downloadPdf}
          disabled={!isApproved}
          className="rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Download PDF
        </button>

        <button
          type="button"
          onClick={exportExcel}
          className="rounded-xl bg-slate-800 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-700"
        >
          Export Excel
        </button>

        <button
          type="button"
          onClick={createOrder}
          disabled={!isApproved}
          className="rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Create ERP Order
        </button>

        <button
          type="button"
          onClick={emailCustomer}
          className="rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-800 transition hover:bg-slate-50"
        >
          Email Customer
        </button>
      </div>

      {!isApproved && !isRejected && (
        <p className="mt-4 text-xs text-slate-500">
          Approve the quote before downloading the PDF or creating
          an ERP order.
        </p>
      )}
    </div>
  );
}