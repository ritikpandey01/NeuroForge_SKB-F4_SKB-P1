"""Generate realistic-looking utility bills as PDFs for testing the AI document parser.

Run from repo root with the backend venv:
    backend/.venv/bin/python samples/bills/generate_bills.py

Outputs into the same directory:
    - electricity_bill_pune_jan2025.pdf       (Scope 2)
    - diesel_invoice_chennai_feb2025.pdf      (Scope 1)
    - natural_gas_bill_chennai_mar2025.pdf    (Scope 1)
    - steel_invoice_jsw_apr2025.pdf           (Scope 3 · materials)
    - freight_invoice_gati_apr2025.pdf        (Scope 3 · freight)
    - flight_itinerary_indigo_mar2025.pdf     (Scope 3 · business travel)
    - waste_disposal_chennai_feb2025.pdf      (Scope 3 · waste)
    - electricity_bill_mumbai_feb2025.pdf     (Scope 2 · BEST)
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT_DIR = Path(__file__).parent
styles = getSampleStyleSheet()
H1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=16, spaceAfter=4)
H2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=11, spaceAfter=2)
P = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9, leading=12)
SMALL = ParagraphStyle("small", parent=styles["BodyText"], fontSize=8, textColor=colors.grey)


def _kv_table(rows: list[tuple[str, str]], col_widths=(55 * mm, 95 * mm)):
    t = Table(rows, colWidths=col_widths)
    t.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def _data_table(header: list[str], rows: list[list[str]]):
    data = [header] + rows
    t = Table(data, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4d3a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f4f4")]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def electricity_bill():
    out = OUT_DIR / "electricity_bill_pune_jan2025.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm)
    story = []
    story.append(Paragraph("MAHARASHTRA STATE ELECTRICITY DISTRIBUTION CO. LTD.", H1))
    story.append(Paragraph("HT Industrial Tariff · Pune Urban Circle", H2))
    story.append(Paragraph("MSEDCL · CIN: U40109MH2005SGC153645 · GSTIN: 27AAECM2933K1ZB", SMALL))
    story.append(Spacer(1, 8))

    story.append(
        _kv_table(
            [
                ("Consumer No.", "170010012345"),
                ("Consumer Name", "Greenfield Manufacturing Pvt. Ltd."),
                ("Service Address", "Plot G-12, MIDC Chakan Phase II, Pune 410501"),
                ("Tariff Category", "HT-I (Industrial)"),
                ("Sanctioned Load", "850 kVA"),
                ("Bill Number", "MSEDCL-INV-202501-PUN-0034521"),
                ("Bill Date", "05 February 2025"),
                ("Billing Period", "01 Jan 2025 – 31 Jan 2025"),
                ("Due Date", "20 February 2025"),
            ]
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Energy Consumption", H2))
    story.append(
        _data_table(
            ["Description", "Previous Reading", "Current Reading", "Multiplier", "Units (kWh)"],
            [
                ["Active Energy (kWh)", "4,182,400", "4,364,800", "1.00", "182,400"],
                ["Reactive Energy (kVArh)", "—", "—", "—", "32,140"],
                ["Maximum Demand (kVA)", "—", "—", "—", "742"],
            ],
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Charges", H2))
    story.append(
        _data_table(
            ["Item", "Rate", "Quantity", "Amount (INR)"],
            [
                ["Energy Charges", "₹7.85 / kWh", "182,400 kWh", "1,431,840.00"],
                ["Demand Charges", "₹420 / kVA", "742 kVA", "311,640.00"],
                ["Wheeling Charges", "₹1.30 / kWh", "182,400 kWh", "237,120.00"],
                ["Fuel Adjustment Charge", "₹0.42 / kWh", "182,400 kWh", "76,608.00"],
                ["Electricity Duty", "9.3% on energy", "—", "133,161.12"],
                ["Tax on Sale", "₹0.26 / kWh", "182,400 kWh", "47,424.00"],
                ["TOTAL PAYABLE", "", "", "2,237,793.12"],
            ],
        )
    )
    story.append(Spacer(1, 12))
    story.append(Paragraph("Pay online at www.mahadiscom.in or via NEFT to A/c 0123456789 (HDFC).", SMALL))
    doc.build(story)
    print(f"  ✓ {out.name}")


def diesel_invoice():
    out = OUT_DIR / "diesel_invoice_chennai_feb2025.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm)
    story = []
    story.append(Paragraph("INDIAN OIL CORPORATION LIMITED", H1))
    story.append(Paragraph("Bulk Diesel Supply · Sriperumbudur Depot", H2))
    story.append(Paragraph("IOCL · CIN: L23201MH1959GOI011388 · GSTIN: 33AAACI1681G1Z3", SMALL))
    story.append(Spacer(1, 8))

    story.append(
        _kv_table(
            [
                ("Customer", "Greenfield Manufacturing Pvt. Ltd."),
                ("Delivery Address", "SIPCOT Industrial Park, Sriperumbudur, Chennai 602105"),
                ("Customer Code", "IOCL-CHN-IND-008842"),
                ("Invoice No.", "IOCL-RB-202502-CHN-7821"),
                ("Invoice Date", "28 February 2025"),
                ("Delivery Period", "01 Feb 2025 – 28 Feb 2025"),
                ("Product", "High Speed Diesel (HSD) — BS-VI"),
            ]
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Delivery Schedule", H2))
    story.append(
        _data_table(
            ["Date", "DC No.", "Vehicle", "Litres", "Rate/L (INR)", "Amount (INR)"],
            [
                ["2025-02-04", "DC-7411", "TN-22-AC-1188", "1,420", "92.40", "131,208.00"],
                ["2025-02-12", "DC-7488", "TN-22-AC-1042", "1,200", "92.40", "110,880.00"],
                ["2025-02-22", "DC-7560", "TN-22-AC-1188", "1,500", "92.65", "138,975.00"],
                ["TOTAL DIESEL DELIVERED", "", "", "4,120 L", "", "381,063.00"],
            ],
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Tax Summary", H2))
    story.append(
        _data_table(
            ["Item", "Amount (INR)"],
            [
                ["Subtotal (4,120 L × avg ₹92.49)", "381,063.00"],
                ["Central Excise Duty (incl. in price)", "—"],
                ["VAT @ 25% (Tamil Nadu)", "95,265.75"],
                ["TCS @ 0.1%", "381.06"],
                ["GRAND TOTAL", "476,709.81"],
            ],
        )
    )
    story.append(Spacer(1, 12))
    story.append(Paragraph("Used for: 250 kVA standby DG set · Plant 1 main building.", SMALL))
    doc.build(story)
    print(f"  ✓ {out.name}")


def natural_gas_bill():
    out = OUT_DIR / "natural_gas_bill_chennai_mar2025.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm)
    story = []
    story.append(Paragraph("GAIL (India) Limited", H1))
    story.append(Paragraph("Industrial Natural Gas Supply · Tamil Nadu Region", H2))
    story.append(Paragraph("GAIL · CIN: L40200DL1984GOI018976 · GSTIN: 33AAACG1209J1ZH", SMALL))
    story.append(Spacer(1, 8))

    story.append(
        _kv_table(
            [
                ("Consumer", "Greenfield Manufacturing Pvt. Ltd."),
                ("Plant", "Chennai Factory · SIPCOT Sriperumbudur"),
                ("Consumer ID", "GAIL-CHN-IND-2241"),
                ("Connection Type", "PNG — Industrial (Process Heating)"),
                ("Invoice No.", "GAIL-INV-202503-CHN-1188"),
                ("Invoice Date", "03 April 2025"),
                ("Billing Period", "01 Mar 2025 – 31 Mar 2025"),
                ("Meter Serial", "GM-IND-77441"),
            ]
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Consumption Details", H2))
    story.append(
        _data_table(
            ["Description", "Reading", "Value"],
            [
                ["Opening reading (m³)", "01-Mar-2025 06:00", "884,210"],
                ["Closing reading (m³)", "31-Mar-2025 06:00", "896,810"],
                ["Volume consumed (m³)", "—", "12,600"],
                ["Calorific value (avg)", "—", "9,250 kcal/m³"],
                ["Energy delivered", "—", "116.55 GJ"],
            ],
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Charges", H2))
    story.append(
        _data_table(
            ["Item", "Rate", "Quantity", "Amount (INR)"],
            [
                ["Gas charges", "₹38.20 / m³", "12,600 m³", "481,320.00"],
                ["Network tariff", "₹3.10 / m³", "12,600 m³", "39,060.00"],
                ["Marketing margin", "₹1.20 / m³", "12,600 m³", "15,120.00"],
                ["GST @ 18%", "—", "—", "96,408.00"],
                ["TOTAL PAYABLE", "", "", "631,908.00"],
            ],
        )
    )
    story.append(Spacer(1, 12))
    story.append(Paragraph("Used for: process boiler & heat treatment furnace.", SMALL))
    doc.build(story)
    print(f"  ✓ {out.name}")


def steel_invoice():
    out = OUT_DIR / "steel_invoice_jsw_apr2025.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm)
    story = []
    story.append(Paragraph("JSW STEEL LIMITED", H1))
    story.append(Paragraph("Tax Invoice · Hot-Rolled Coil Supply", H2))
    story.append(Paragraph("JSW · CIN: L27102MH1994PLC152925 · GSTIN: 27AAACJ4323N1ZP", SMALL))
    story.append(Spacer(1, 8))

    story.append(
        _kv_table(
            [
                ("Buyer", "Greenfield Manufacturing Pvt. Ltd."),
                ("Ship-to", "Plot G-12, MIDC Chakan Phase II, Pune 410501"),
                ("PO Reference", "JSW-PO-2025-0142"),
                ("Invoice No.", "JSW-INV-2025-04-771229"),
                ("Invoice Date", "12 April 2025"),
                ("Vehicle / E-way Bill", "MH-14-EH-7822 / EWB 178822334411"),
                ("Material Grade", "IS 2062 E250 BR — HRC 4.0mm × 1250mm"),
            ]
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Material Delivered", H2))
    story.append(
        _data_table(
            ["Item", "HSN", "Quantity", "Rate (INR/MT)", "Amount (INR)"],
            [
                ["HRC 4.0mm Coils — IS 2062 E250 BR", "72083920", "412.500 MT", "57,200.00", "23,595,000.00"],
                ["HRC 3.0mm Coils — IS 2062 E250 BR", "72083920", "207.500 MT", "57,800.00", "11,993,500.00"],
                ["TOTAL MATERIAL", "", "620.000 MT", "", "35,588,500.00"],
            ],
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Tax Summary", H2))
    story.append(
        _data_table(
            ["Item", "Rate", "Amount (INR)"],
            [
                ["Sub-total", "—", "35,588,500.00"],
                ["IGST", "18%", "6,405,930.00"],
                ["TCS", "0.1%", "35,588.50"],
                ["GRAND TOTAL", "—", "42,030,018.50"],
            ],
        )
    )
    story.append(Spacer(1, 12))
    story.append(Paragraph("Despatched ex-Vijayanagar Works · Net delivered weight 620,000 kg.", SMALL))
    doc.build(story)
    print(f"  ✓ {out.name}")


def freight_invoice():
    out = OUT_DIR / "freight_invoice_gati_apr2025.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm)
    story = []
    story.append(Paragraph("GATI-KWE LIMITED", H1))
    story.append(Paragraph("Inbound Logistics Invoice · Surface Express", H2))
    story.append(Paragraph("Gati · CIN: L63011TG1995PLC020121 · GSTIN: 36AABCG2436N1Z3", SMALL))
    story.append(Spacer(1, 8))

    story.append(
        _kv_table(
            [
                ("Customer", "Greenfield Manufacturing Pvt. Ltd."),
                ("Account No.", "GATI-CUST-008842"),
                ("Invoice No.", "GATI-INV-2025-04-091156"),
                ("Invoice Date", "30 April 2025"),
                ("Service Period", "01 Apr 2025 – 30 Apr 2025"),
                ("Service Type", "Full-truck-load (FTL) road freight"),
            ]
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Consignment Summary", H2))
    story.append(
        _data_table(
            ["LR No.", "Origin → Destination", "Distance (km)", "Cargo (MT)", "Tonne-km", "Amount (INR)"],
            [
                ["LR-7741", "Vijayanagar (KA) → Pune", "650", "210.0", "136,500", "182,000.00"],
                ["LR-7798", "Vijayanagar (KA) → Pune", "650", "205.0", "133,250", "178,200.00"],
                ["LR-7841", "Mumbai Port → Pune", "165", "82.0", "13,530", "44,000.00"],
                ["LR-7902", "Sriperumbudur → Chennai port", "55", "42.0", "2,310", "12,000.00"],
                ["TOTAL", "", "", "539.0 MT", "285,590", "416,200.00"],
            ],
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Charges", H2))
    story.append(
        _data_table(
            ["Item", "Amount (INR)"],
            [
                ["Sub-total freight", "416,200.00"],
                ["GST @ 12% (RCM applicable)", "49,944.00"],
                ["GRAND TOTAL", "466,144.00"],
            ],
        )
    )
    story.append(Spacer(1, 12))
    story.append(Paragraph("Mode of transport: BS-VI HGV (16-22 MT capacity). Single-axle and tridem mix.", SMALL))
    doc.build(story)
    print(f"  ✓ {out.name}")


def flight_itinerary():
    out = OUT_DIR / "flight_itinerary_indigo_mar2025.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm)
    story = []
    story.append(Paragraph("INDIGO 6E — TRAVEL ITINERARY", H1))
    story.append(Paragraph("Corporate Booking · GST Invoice attached", H2))
    story.append(Paragraph("InterGlobe Aviation Ltd · CIN: L62100DL2004PLC129768 · GSTIN: 06AABCI2726B1Z8", SMALL))
    story.append(Spacer(1, 8))

    story.append(
        _kv_table(
            [
                ("Booked by", "Greenfield Manufacturing Pvt. Ltd. — Travel Desk"),
                ("Corporate Account", "INDIGO-CORP-44712"),
                ("PNR", "Q8K2RT"),
                ("Booking Reference", "BR-2025-03-178821"),
                ("Booking Date", "08 March 2025"),
                ("Passengers", "5 (Sales & BD team — Mumbai HQ)"),
            ]
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Flight Segments", H2))
    story.append(
        _data_table(
            ["Date", "Flight", "Sector", "Distance (km)", "Pax", "Pax-km"],
            [
                ["12-Mar-2025", "6E-2031", "BOM → BLR (Mumbai – Bangalore)", "842", "5", "4,210"],
                ["14-Mar-2025", "6E-5544", "BLR → DEL (Bangalore – Delhi)", "1,748", "5", "8,740"],
                ["15-Mar-2025", "6E-2155", "DEL → BOM (Delhi – Mumbai)", "1,138", "5", "5,690"],
                ["TOTAL DOMESTIC", "", "", "3,728", "5", "18,640"],
            ],
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Fare Summary", H2))
    story.append(
        _data_table(
            ["Item", "Amount (INR)"],
            [
                ["Base fare (5 pax × 3 segments)", "187,500.00"],
                ["Fuel surcharge", "42,000.00"],
                ["User Development Fee", "8,250.00"],
                ["GST @ 5%", "11,888.00"],
                ["GRAND TOTAL", "249,638.00"],
            ],
        )
    )
    story.append(Spacer(1, 12))
    story.append(Paragraph("Total domestic passenger-km: 18,640. Cabin class: Economy.", SMALL))
    doc.build(story)
    print(f"  ✓ {out.name}")


def waste_disposal_receipt():
    out = OUT_DIR / "waste_disposal_chennai_feb2025.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm)
    story = []
    story.append(Paragraph("RAMKY ENVIRO ENGINEERS LTD.", H1))
    story.append(Paragraph("Industrial Waste Disposal Receipt · TNPCB-Authorised Handler", H2))
    story.append(Paragraph("Ramky · CIN: U74900TG1994PLC017369 · TNPCB Reg: TNHWM-2024-1188", SMALL))
    story.append(Spacer(1, 8))

    story.append(
        _kv_table(
            [
                ("Generator", "Greenfield Manufacturing Pvt. Ltd."),
                ("Generator Site", "SIPCOT Industrial Park, Sriperumbudur, Chennai 602105"),
                ("Receipt No.", "RAMKY-WD-202502-7811"),
                ("Receipt Date", "27 February 2025"),
                ("Service Period", "01 Feb 2025 – 28 Feb 2025"),
                ("Manifest No.", "TNHWM-MAN-2025-002211"),
            ]
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Waste Streams Collected", H2))
    story.append(
        _data_table(
            ["Stream", "Treatment Path", "Quantity (kg)", "Charge (INR)"],
            [
                ["Mixed industrial / non-hazardous", "Landfill (TNPCB-approved)", "2,400", "14,400.00"],
                ["Recyclable metals (steel scrap)", "Recycling — sold to JSW Steel", "1,820", "(credit) -27,300.00"],
                ["Process sludge (cat-A)", "Incineration (Hyderabad TSDF)", "640", "32,000.00"],
                ["Cardboard / paper packaging", "Recycling", "880", "(credit) -3,520.00"],
                ["TOTAL", "", "5,740", "15,580.00"],
            ],
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Tax Summary", H2))
    story.append(
        _data_table(
            ["Item", "Amount (INR)"],
            [
                ["Net service value", "15,580.00"],
                ["GST @ 18%", "2,804.40"],
                ["GRAND TOTAL", "18,384.40"],
            ],
        )
    )
    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            "All hazardous waste manifests filed with TNPCB. Recyclable streams routed to authorised re-processors.",
            SMALL,
        )
    )
    doc.build(story)
    print(f"  ✓ {out.name}")


def mumbai_electricity_bill():
    out = OUT_DIR / "electricity_bill_mumbai_feb2025.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm)
    story = []
    story.append(Paragraph("BRIHANMUMBAI ELECTRIC SUPPLY & TRANSPORT (BEST)", H1))
    story.append(Paragraph("Commercial Tariff · Bandra-Kurla Complex Division", H2))
    story.append(Paragraph("BEST Undertaking · GSTIN: 27AAALB0382L1ZH", SMALL))
    story.append(Spacer(1, 8))

    story.append(
        _kv_table(
            [
                ("Consumer No.", "270450091188"),
                ("Consumer Name", "Greenfield Manufacturing Pvt. Ltd."),
                ("Service Address", "B-Wing, 14th Floor, Trade Tower, BKC, Mumbai 400051"),
                ("Tariff Category", "LT-II (Commercial > 20 kW)"),
                ("Sanctioned Load", "65 kW"),
                ("Bill Number", "BEST-INV-202502-BKC-0119887"),
                ("Bill Date", "06 March 2025"),
                ("Billing Period", "01 Feb 2025 – 28 Feb 2025"),
                ("Due Date", "21 March 2025"),
            ]
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Energy Consumption", H2))
    story.append(
        _data_table(
            ["Description", "Previous Reading", "Current Reading", "Multiplier", "Units (kWh)"],
            [
                ["Active Energy", "284,512", "302,891", "1.00", "18,379"],
                ["Reactive Energy (kVArh)", "—", "—", "—", "3,250"],
            ],
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Charges", H2))
    story.append(
        _data_table(
            ["Item", "Rate", "Quantity", "Amount (INR)"],
            [
                ["Energy Charges (slab 1: 0-500)", "₹6.20 / kWh", "500 kWh", "3,100.00"],
                ["Energy Charges (slab 2: >500)", "₹11.85 / kWh", "17,879 kWh", "211,866.15"],
                ["Fixed Charges", "₹290 / kW", "65 kW", "18,850.00"],
                ["Wheeling Charges", "₹1.84 / kWh", "18,379 kWh", "33,817.36"],
                ["Electricity Duty", "16%", "—", "42,165.36"],
                ["Tax on Sale", "₹0.16 / kWh", "18,379 kWh", "2,940.64"],
                ["TOTAL PAYABLE", "", "", "312,739.51"],
            ],
        )
    )
    story.append(Spacer(1, 12))
    story.append(Paragraph("Pay online at www.bestundertaking.com or via UPI to bestbilling@hdfcbank.", SMALL))
    doc.build(story)
    print(f"  ✓ {out.name}")


if __name__ == "__main__":
    print("Generating sample utility bills…")
    electricity_bill()
    diesel_invoice()
    natural_gas_bill()
    steel_invoice()
    freight_invoice()
    flight_itinerary()
    waste_disposal_receipt()
    mumbai_electricity_bill()
    print(f"\nAll PDFs written to: {OUT_DIR}")
