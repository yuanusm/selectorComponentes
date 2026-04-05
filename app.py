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
              1e-6, 2.2e-6, 4.7e-6, 1e-5, 2.2e-5, 4.7e-5]

    mejores = []

    for R1, R2 in itertools.product(R_list, repeat=2):
        if R2 < 100 or R1 < 100:
            continue
        k = R1 / R2
        err_k = abs(k - k_target) / k_target
        if err_k > tol * 1.5:
            continue

        for Ra in [r for r in R_list if r >= 560]:
            Cf_ideal = P_target / Ra
            Cf = min(C_list, key=lambda c: abs(c - Cf_ideal))

            H_calc = 2 * (R1 / R2) * Vcc
            f_calc = Vcc / (2 * H_calc * Ra * Cf) if H_calc > 0 else 0

            err_total = max(abs(H_calc - H_target)/H_target if H_target else 0,
                            abs(f_calc - f_target)/f_target if f_target else 0)

            if err_total <= tol:
                mejores.append({
                    "R1": R1, "R2": R2, "Ra": Ra, "Cf": Cf * 1e9,
                    "H_calc": round(H_calc, 3),
                    "f_calc": round(f_calc, 2),
                    "error_%": round(err_total * 100, 2)
                })

    return sorted(mejores, key=lambda x: x["error_%"])[:top_n]


class App(CTk):
    def __init__(self):
        super().__init__()

        self.title("Selector de Componentes")
        self.geometry("420x420")
        self.minsize(400, 400)

        # Fonts compactas
        self.f_title = ctk.CTkFont(size=15, weight="bold")
        self.f_label = ctk.CTkFont(size=11)
        self.f_input = ctk.CTkFont(size=11)
        self.f_btn = ctk.CTkFont(size=12, weight="bold")
        self.f_mono = ctk.CTkFont(family="Consolas", size=10)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main = CTkFrame(self, corner_radius=0, fg_color="transparent")
        main.grid(row=0, column=0, sticky="nsew", padx=8, pady=6)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(4, weight=1)

        # Toolbar
        toolbar = CTkFrame(main, corner_radius=8, fg_color=("#222834", "#1B2230"))
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        toolbar.grid_columnconfigure(1, weight=1)

        CTkLabel(toolbar, text="Circuito", font=self.f_label).grid(row=0, column=0, padx=(8, 4), pady=5)
        self.circuit_var = ctk.StringVar(value="Oscilador triangular")
        self.circuit_menu = CTkOptionMenu(
            toolbar,
            values=["Oscilador triangular", "Filtro RC", "Amplificador"],
            variable=self.circuit_var,
            height=26,
            font=self.f_input,
            dropdown_font=self.f_input,
            anchor="w",
        )
        self.circuit_menu.grid(row=0, column=1, padx=(0, 8), pady=5, sticky="ew")

        # Title
        CTkLabel(
            main,
            text="Calculadora de valores comerciales",
            font=self.f_title,
            anchor="w"
        ).grid(row=1, column=0, sticky="w", pady=(0, 4), padx=2)

        # Input panel
        inputs = CTkFrame(main, corner_radius=10, fg_color=("#1D222D", "#181D27"))
        inputs.grid(row=2, column=0, sticky="ew", pady=(0, 5))
        inputs.grid_columnconfigure(1, weight=1)

        label_pad = {"padx": (8, 6), "pady": 3}
        entry_pad = {"padx": (0, 8), "pady": 3}

        CTkLabel(inputs, text="Frecuencia (Hz)", font=self.f_label).grid(row=0, column=0, sticky="e", **label_pad)
        self.f_entry = CTkEntry(inputs, height=26, font=self.f_input)
        self.f_entry.grid(row=0, column=1, sticky="ew", **entry_pad)
        self.f_entry.insert(0, "1000")

        CTkLabel(inputs, text="Histeresis (Vpp)", font=self.f_label).grid(row=1, column=0, sticky="e", **label_pad)
        self.h_entry = CTkEntry(inputs, height=26, font=self.f_input)
        self.h_entry.grid(row=1, column=1, sticky="ew", **entry_pad)
        self.h_entry.insert(0, "5")

        CTkLabel(inputs, text="Vcc (V)", font=self.f_label).grid(row=2, column=0, sticky="e", **label_pad)
        self.vcc_entry = CTkEntry(inputs, height=26, font=self.f_input)
        self.vcc_entry.grid(row=2, column=1, sticky="ew", **entry_pad)
        self.vcc_entry.insert(0, "12")

        CTkLabel(inputs, text="Tolerancia (%)", font=self.f_label).grid(row=3, column=0, sticky="e", **label_pad)
        self.tol_entry = CTkEntry(inputs, height=26, font=self.f_input)
        self.tol_entry.grid(row=3, column=1, sticky="ew", **entry_pad)
        self.tol_entry.insert(0, "5")

        CTkLabel(inputs, text="Serie", font=self.f_label).grid(row=4, column=0, sticky="e", **label_pad)
        self.serie_var = ctk.StringVar(value="E24")
        self.serie_menu = CTkOptionMenu(
            inputs,
            values=["E12", "E24"],
            variable=self.serie_var,
            height=26,
            font=self.f_input,
            dropdown_font=self.f_input,
            anchor="w",
        )
        self.serie_menu.grid(row=4, column=1, sticky="w", **entry_pad)

        # Primary action button
        self.btn_calcular = CTkButton(
            main,
            text="Calcular",
            command=self.calcular,
            height=30,
            width=140,
            font=self.f_btn,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            corner_radius=8,
        )
        self.btn_calcular.grid(row=3, column=0, pady=(0, 5))

        # Results panel
        self.textbox = CTkTextbox(
            main,
            font=self.f_mono,
            corner_radius=8,
            border_width=1,
            border_color="#2A2F3A",
            wrap="none",
        )
        self.textbox.grid(row=4, column=0, sticky="nsew", padx=1, pady=(0, 0))

        self._set_initial_message()

    def _set_initial_message(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert(
            "end",
            "Sistema listo.\n"
            "Selecciona circuito, ingresa parámetros y presiona Calcular.\n"
        )
        self.textbox.configure(state="disabled")

    def calcular(self):
        try:
            f = float(self.f_entry.get())
            H = float(self.h_entry.get())
            Vcc = float(self.vcc_entry.get())
            tol = float(self.tol_entry.get()) / 100.0
            serie = self.serie_var.get()
            circuito = self.circuit_var.get()

            if f <= 0 or H <= 0 or Vcc <= 0 or tol <= 0:
                raise ValueError("Los valores deben ser positivos")

            self.textbox.configure(state="normal")
            self.textbox.delete("1.0", "end")
            self.textbox.insert("end", f"Circuito: {circuito}\n")
            self.textbox.insert("end", f"f = {f} Hz | H = {H} V | Vcc = {Vcc} V | Tol ≤ {tol*100:.1f}%\n")
            self.textbox.insert("end", f"Serie: {serie}\n\n")
            self.textbox.insert("end", "Calculando...\n\n")
            self.update()

            resultados = seleccionar_componentes(f, H, Vcc, tol=tol, serie=serie, top_n=20)

            self.textbox.delete("1.0", "end")
            if not resultados:
                self.textbox.insert("end", "No se encontraron combinaciones dentro de la tolerancia.\n")
                self.textbox.insert("end", "Intenta aumentar la tolerancia o cambiar los valores.")
            else:
                self.textbox.insert("end", f"{len(resultados)} combinaciones válidas:\n\n")
                self.textbox.insert(
                    "end",
                    f"{'R1':>8} {'R2':>8} {'Ra':>8} {'Cf(nF)':>8} {'H':>8} {'f(Hz)':>10} {'Err%':>7}\n"
                )
                self.textbox.insert("end", "-" * 70 + "\n")
                for r in resultados:
                    self.textbox.insert(
                        "end",
                        f"{r['R1']:>8.1f} {r['R2']:>8.1f} {r['Ra']:>8.1f} {r['Cf']:>8.2f} "
                        f"{r['H_calc']:>8.3f} {r['f_calc']:>10.2f} {r['error_%']:>7.2f}\n"
                    )
                self.textbox.insert("end", "\nRecomendación: elegir menor Error (%).")

            self.textbox.configure(state="disabled")

        except ValueError as e:
            self.textbox.configure(state="normal")
            self.textbox.delete("1.0", "end")
            self.textbox.insert("end", f"Error: {str(e)}\nPor favor ingresa números válidos.")
            self.textbox.configure(state="disabled")


if __name__ == "__main__":
    app = App()
    app.mainloop()
