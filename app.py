import customtkinter as ctk
from customtkinter import CTk, CTkLabel, CTkEntry, CTkButton, CTkOptionMenu, CTkTextbox, CTkFrame
import itertools

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def generar_e_series(serie="E24", max_decadas=6):
    if serie == "E24":
        base = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
                3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
    else:  # E12 más simple
        base = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]

    valores = []
    for dec in range(max_decadas + 1):
        for b in base:
            val = round(b * (10 ** dec), 2)
            if val > 10_000_000:
                continue
            valores.append(val)
    return sorted(set(valores))


def seleccionar_componentes(f_target, H_target, Vcc, tol=0.05, serie="E24", top_n=15):
    k_target = H_target / (2 * Vcc)
    P_target = Vcc / (2 * H_target * f_target)

    R_list = generar_e_series(serie, max_decadas=6)
    C_list = [1e-12, 2.2e-12, 4.7e-12, 1e-11, 2.2e-11, 4.7e-11, 1e-10, 2.2e-10, 4.7e-10,
              1e-9, 2.2e-9, 4.7e-9, 1e-8, 2.2e-8, 4.7e-8, 1e-7, 2.2e-7, 4.7e-7,
              1e-6, 2.2e-6, 4.7e-6, 1e-5, 2.2e-5, 4.7e-5]  # pF a ~47µF

    mejores = []

    for R1, R2 in itertools.product(R_list, repeat=2):
        if R2 < 100 or R1 < 100:
            continue  # evitar valores muy pequeños
        k = R1 / R2
        err_k = abs(k - k_target) / k_target
        if err_k > tol * 1.5:
            continue

        for Ra in [r for r in R_list if r >= 560]:
            Cf_ideal = P_target / Ra
            # Cf comercial más cercano
            Cf = min(C_list, key=lambda c: abs(c - Cf_ideal))

            H_calc = 2 * (R1 / R2) * Vcc
            f_calc = Vcc / (2 * H_calc * Ra * Cf) if H_calc > 0 else 0

            err_total = max(abs(H_calc - H_target)/H_target if H_target else 0,
                            abs(f_calc - f_target)/f_target if f_target else 0)

            if err_total <= tol:
                mejores.append({
                    "R1": R1, "R2": R2, "Ra": Ra, "Cf": Cf * 1e9,  # en nF para mejor lectura
                    "H_calc": round(H_calc, 3),
                    "f_calc": round(f_calc, 2),
                    "error_%": round(err_total * 100, 2)
                })

    # Ordenar por menor error
    mejores = sorted(mejores, key=lambda x: x["error_%"])[:top_n]
    return mejores


class App(CTk):
    def __init__(self):
        super().__init__()
        self.title("Selector de Componentes")
        self.geometry("420x420")
        self.resizable(False, False)

        self.font_toolbar = ctk.CTkFont(size=10)
        self.font_title = ctk.CTkFont(size=13, weight="bold")
        self.font_label = ctk.CTkFont(size=11)
        self.font_entry = ctk.CTkFont(size=11)
        self.font_button = ctk.CTkFont(size=12, weight="bold")
        self.font_result = ctk.CTkFont(family="Consolas", size=10)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        main = CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(4, weight=1)  # solo resultados expande

        # [ Toolbar (very thin) ]
        toolbar = CTkFrame(main, corner_radius=6, fg_color=("#202632", "#1B2130"), height=30)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        toolbar.grid_propagate(False)
        toolbar.grid_columnconfigure(1, weight=1)

        CTkLabel(toolbar, text="Circuito:", font=self.font_toolbar).grid(
            row=0, column=0, padx=(6, 4), pady=2, sticky="w"
        )
        self.circuit_var = ctk.StringVar(value="Oscilador triangular")
        self.circuit_menu = CTkOptionMenu(
            toolbar,
            values=["Oscilador triangular", "Filtro RC", "Amplificador"],
            variable=self.circuit_var,
            height=22,
            font=self.font_toolbar,
            dropdown_font=self.font_toolbar,
            dynamic_resizing=False,
            anchor="w",
        )
        self.circuit_menu.grid(row=0, column=1, padx=(0, 6), pady=2, sticky="ew")

        # [ Title (small) ]
        CTkLabel(
            main,
            text="Calculadora de Valores Comerciales",
            font=self.font_title,
            anchor="center",
        ).grid(row=1, column=0, sticky="ew", pady=(0, 2))

        # [ Input Panel (compact grid) ]
        input_panel = CTkFrame(main, corner_radius=8, fg_color=("#1A1F2A", "#151B26"))
        input_panel.grid(row=2, column=0, sticky="ew", pady=(0, 2))
        input_panel.grid_columnconfigure(0, weight=0)
        input_panel.grid_columnconfigure(1, weight=1)

        lbl_pad = {"padx": (6, 4), "pady": 1}
        ent_pad = {"padx": (0, 6), "pady": 1}

        CTkLabel(input_panel, text="Frecuencia (Hz):", font=self.font_label).grid(row=0, column=0, sticky="e", **lbl_pad)
        self.f_entry = CTkEntry(input_panel, height=24, font=self.font_entry)
        self.f_entry.grid(row=0, column=1, sticky="ew", **ent_pad)
        self.f_entry.insert(0, "1000")

        CTkLabel(input_panel, text="Histeresis (Vpp):", font=self.font_label).grid(row=1, column=0, sticky="e", **lbl_pad)
        self.h_entry = CTkEntry(input_panel, height=24, font=self.font_entry)
        self.h_entry.grid(row=1, column=1, sticky="ew", **ent_pad)
        self.h_entry.insert(0, "5")

        CTkLabel(input_panel, text="Vcc (V):", font=self.font_label).grid(row=2, column=0, sticky="e", **lbl_pad)
        self.vcc_entry = CTkEntry(input_panel, height=24, font=self.font_entry)
        self.vcc_entry.grid(row=2, column=1, sticky="ew", **ent_pad)
        self.vcc_entry.insert(0, "12")

        CTkLabel(input_panel, text="Tolerancia (%):", font=self.font_label).grid(row=3, column=0, sticky="e", **lbl_pad)
        self.tol_entry = CTkEntry(input_panel, height=24, font=self.font_entry)
        self.tol_entry.grid(row=3, column=1, sticky="ew", **ent_pad)
        self.tol_entry.insert(0, "5")

        CTkLabel(input_panel, text="Serie:", font=self.font_label).grid(row=4, column=0, sticky="e", **lbl_pad)
        self.serie_var = ctk.StringVar(value="E24")
        self.serie_menu = CTkOptionMenu(
            input_panel,
            values=["E12", "E24"],
            variable=self.serie_var,
            height=24,
            font=self.font_entry,
            dropdown_font=self.font_entry,
            dynamic_resizing=False,
            anchor="w",
        )
        self.serie_menu.grid(row=4, column=1, sticky="w", **ent_pad)

        # [ Action Button ]
        self.btn_calcular = CTkButton(
            main,
            text="Calcular",
            font=self.font_button,
            width=140,
            height=28,
            corner_radius=8,
            command=self.calcular,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
        )
        self.btn_calcular.grid(row=3, column=0, pady=(0, 2))

        # [ Results Panel (fills remaining space) ]
        self.textbox = CTkTextbox(
            main,
            font=self.font_result,
            wrap="none",
            corner_radius=8,
            border_width=1,
            border_color="#2A2F3A",
        )
        self.textbox.grid(row=4, column=0, sticky="nsew", padx=0, pady=0)

        self.textbox.insert("0.0", "Sistema listo. Ingresa parámetros y presiona Calcular.\n")
        self.textbox.configure(state="disabled")

    def calcular(self):
        try:
            f = float(self.f_entry.get())
            H = float(self.h_entry.get())
            Vcc = float(self.vcc_entry.get())
            tol = float(self.tol_entry.get()) / 100.0
            serie = self.serie_var.get()

            if f <= 0 or H <= 0 or Vcc <= 0 or tol <= 0:
                raise ValueError("Los valores deben ser positivos")

            self.textbox.configure(state="normal")
            self.textbox.delete("1.0", "end")
            self.textbox.insert("end", f"Buscando combinaciones para:\n")
            self.textbox.insert("end", f"Circuito: {self.circuit_var.get()}\n")
            self.textbox.insert("end", f"f={f} Hz | H={H} V | Vcc={Vcc} V | Tol≤{tol*100:.1f}%\n")
            self.textbox.insert("end", f"Serie: {serie}\n\n")
            self.textbox.insert("end", "Calculando...\n\n")
            self.update()

            resultados = seleccionar_componentes(f, H, Vcc, tol=tol, serie=serie, top_n=20)

            self.textbox.delete("1.0", "end")
            if not resultados:
                self.textbox.insert("end", "No se encontraron combinaciones dentro de la tolerancia.\n")
                self.textbox.insert("end", "Intenta aumentar la tolerancia o cambiar los valores.")
            else:
                self.textbox.insert("end", f"Se encontraron {len(resultados)} combinaciones válidas:\n\n")
                self.textbox.insert("end", "R1(Ω)    R2(Ω)    Ra(Ω)    Cf(nF)    H_calc    f_calc(Hz)   Error(%)\n")
                self.textbox.insert("end", "-" * 76 + "\n")

                for r in resultados:
                    linea = f"{r['R1']:>7.1f}  {r['R2']:>7.1f}  {r['Ra']:>7.1f}  {r['Cf']:>8.2f}  "
                    linea += f"{r['H_calc']:>8.3f}  {r['f_calc']:>10.2f}  {r['error_%']:>8.2f}\n"
                    self.textbox.insert("end", linea)

                self.textbox.insert("end", "\nRecomendación: Elige la fila con menor Error (%).")

            self.textbox.configure(state="disabled")

        except ValueError as e:
            self.textbox.configure(state="normal")
            self.textbox.delete("1.0", "end")
            self.textbox.insert("end", f"Error: {str(e)}\nPor favor ingresa números válidos.")
            self.textbox.configure(state="disabled")


if __name__ == "__main__":
    app = App()
    app.mainloop()
