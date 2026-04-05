import customtkinter as ctk
from customtkinter import CTk, CTkLabel, CTkEntry, CTkButton, CTkOptionMenu, CTkTextbox, CTkFrame
import itertools

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def generar_e_series(serie="E24", max_decadas=6):
    if serie == "E24":
        base = [
            1.0,
            1.1,
            1.2,
            1.3,
            1.5,
            1.6,
            1.8,
            2.0,
            2.2,
            2.4,
            2.7,
            3.0,
            3.3,
            3.6,
            3.9,
            4.3,
            4.7,
            5.1,
            5.6,
            6.2,
            6.8,
            7.5,
            8.2,
            9.1,
        ]
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
    C_list = [
        1e-12,
        2.2e-12,
        4.7e-12,
        1e-11,
        2.2e-11,
        4.7e-11,
        1e-10,
        2.2e-10,
        4.7e-10,
        1e-9,
        2.2e-9,
        4.7e-9,
        1e-8,
        2.2e-8,
        4.7e-8,
        1e-7,
        2.2e-7,
        4.7e-7,
        1e-6,
        2.2e-6,
        4.7e-6,
        1e-5,
        2.2e-5,
        4.7e-5,
    ]  # pF a ~47µF

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

            err_total = max(
                abs(H_calc - H_target) / H_target if H_target else 0,
                abs(f_calc - f_target) / f_target if f_target else 0,
            )

            if err_total <= tol:
                mejores.append(
                    {
                        "R1": R1,
                        "R2": R2,
                        "Ra": Ra,
                        "Cf": Cf * 1e9,  # en nF para mejor lectura
                        "H_calc": round(H_calc, 3),
                        "f_calc": round(f_calc, 2),
                        "error_%": round(err_total * 100, 2),
                    }
                )

    # Ordenar por menor error
    mejores = sorted(mejores, key=lambda x: x["error_%"])[:top_n]
    return mejores


class App(CTk):
    def __init__(self):
        super().__init__()

        self.title("Selector de Componentes - Oscilador Triangular")
        self.geometry("1160x800")
        self.minsize(980, 700)

        # Tipografías
        self.font_title = ctk.CTkFont(size=28, weight="bold")
        self.font_subtitle = ctk.CTkFont(size=14)
        self.font_section = ctk.CTkFont(size=16, weight="bold")
        self.font_label = ctk.CTkFont(size=13)
        self.font_entry = ctk.CTkFont(size=13)
        self.font_button = ctk.CTkFont(size=15, weight="bold")
        self.font_mono = ctk.CTkFont(family="Consolas", size=13)

        # Grid principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Contenedor centrado con márgenes
        container = CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=0, padx=30, pady=24, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        # Header
        header = CTkFrame(container, corner_radius=16, fg_color=("#1A1D24", "#151922"))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = CTkLabel(
            header,
            text="Calculadora de Valores Comerciales",
            font=self.font_title,
            anchor="w",
        )
        title.grid(row=0, column=0, padx=24, pady=(18, 2), sticky="w")

        subtitle = CTkLabel(
            header,
            text="Oscilador triangular con Schmitt + Integrador | Diseño asistido por componentes E12/E24",
            font=self.font_subtitle,
            text_color="#A7B0C0",
            anchor="w",
        )
        subtitle.grid(row=1, column=0, padx=24, pady=(0, 16), sticky="w")

        separator = CTkFrame(container, height=2, corner_radius=1, fg_color=("#2A2F3A", "#272C36"))
        separator.grid(row=1, column=0, pady=(14, 14), sticky="ew")

        # Área principal scrollable para mantener responsividad
        content = ctk.CTkScrollableFrame(
            container,
            corner_radius=0,
            fg_color="transparent",
            scrollbar_button_color="#3B82F6",
            scrollbar_button_hover_color="#2563EB",
        )
        content.grid(row=2, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=1)

        # Panel de parámetros
        params_card = CTkFrame(content, corner_radius=18, fg_color=("#1B202A", "#171C25"))
        params_card.grid(row=0, column=0, sticky="ew", padx=8, pady=(2, 14))
        params_card.grid_columnconfigure(0, weight=1)
        params_card.grid_columnconfigure(1, weight=1)

        params_title = CTkLabel(params_card, text="Parámetros", font=self.font_section)
        params_title.grid(row=0, column=0, columnspan=2, padx=22, pady=(18, 10), sticky="w")

        divider_top = CTkFrame(params_card, height=1, fg_color=("#2A2F3A", "#2A2F3A"))
        divider_top.grid(row=1, column=0, columnspan=2, sticky="ew", padx=22, pady=(0, 10))

        field_frame = CTkFrame(params_card, fg_color="transparent")
        field_frame.grid(row=2, column=0, columnspan=2, padx=22, pady=(2, 8), sticky="ew")
        field_frame.grid_columnconfigure(0, weight=0)
        field_frame.grid_columnconfigure(1, weight=1)

        row_gap = {"padx": (0, 12), "pady": 8}
        input_gap = {"padx": (0, 0), "pady": 8}

        CTkLabel(field_frame, text="Frecuencia objetivo (Hz)", font=self.font_label, anchor="e").grid(
            row=0, column=0, sticky="e", **row_gap
        )
        self.f_entry = CTkEntry(field_frame, font=self.font_entry, height=34, placeholder_text="1000")
        self.f_entry.grid(row=0, column=1, sticky="ew", **input_gap)
        self.f_entry.insert(0, "1000")

        CTkLabel(field_frame, text="Histeresis H (Vpp)", font=self.font_label, anchor="e").grid(
            row=1, column=0, sticky="e", **row_gap
        )
        self.h_entry = CTkEntry(field_frame, font=self.font_entry, height=34, placeholder_text="5")
        self.h_entry.grid(row=1, column=1, sticky="ew", **input_gap)
        self.h_entry.insert(0, "5")

        CTkLabel(field_frame, text="Vcc (V)", font=self.font_label, anchor="e").grid(
            row=2, column=0, sticky="e", **row_gap
        )
        self.vcc_entry = CTkEntry(field_frame, font=self.font_entry, height=34, placeholder_text="12")
        self.vcc_entry.grid(row=2, column=1, sticky="ew", **input_gap)
        self.vcc_entry.insert(0, "12")

        CTkLabel(field_frame, text="Tolerancia máxima (%)", font=self.font_label, anchor="e").grid(
            row=3, column=0, sticky="e", **row_gap
        )
        self.tol_entry = CTkEntry(field_frame, font=self.font_entry, height=34, placeholder_text="5")
        self.tol_entry.grid(row=3, column=1, sticky="ew", **input_gap)
        self.tol_entry.insert(0, "5")

        CTkLabel(field_frame, text="Serie de valores", font=self.font_label, anchor="e").grid(
            row=4, column=0, sticky="e", **row_gap
        )
        self.serie_var = ctk.StringVar(value="E24")
        self.serie_menu = CTkOptionMenu(
            field_frame,
            values=["E12", "E24"],
            variable=self.serie_var,
            height=34,
            font=self.font_entry,
            dropdown_font=self.font_entry,
        )
        self.serie_menu.grid(row=4, column=1, sticky="w", **input_gap)

        # Botón principal
        self.btn_calcular = CTkButton(
            params_card,
            text="Calcular Mejores Combinaciones",
            font=self.font_button,
            height=44,
            width=320,
            corner_radius=12,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.calcular,
        )
        self.btn_calcular.grid(row=3, column=0, columnspan=2, pady=(10, 20))

        # Panel de resultados
        result_card = CTkFrame(content, corner_radius=18, fg_color=("#1B202A", "#171C25"))
        result_card.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        result_card.grid_columnconfigure(0, weight=1)
        result_card.grid_rowconfigure(2, weight=1)

        result_title = CTkLabel(result_card, text="Resultados", font=self.font_section)
        result_title.grid(row=0, column=0, padx=22, pady=(18, 8), sticky="w")

        result_subtitle = CTkLabel(
            result_card,
            text="Combinaciones ordenadas por menor error total",
            font=self.font_subtitle,
            text_color="#A7B0C0",
        )
        result_subtitle.grid(row=1, column=0, padx=22, pady=(0, 10), sticky="w")

        divider_bottom = CTkFrame(result_card, height=1, fg_color=("#2A2F3A", "#2A2F3A"))
        divider_bottom.grid(row=2, column=0, sticky="ew", padx=22, pady=(0, 12))

        self.textbox = CTkTextbox(
            result_card,
            height=380,
            corner_radius=12,
            font=self.font_mono,
            border_width=1,
            border_color="#2A2F3A",
            fg_color=("#11151D", "#0F141C"),
            wrap="none",
        )
        self.textbox.grid(row=3, column=0, padx=22, pady=(0, 22), sticky="nsew")

        self._set_initial_message()

    def _set_initial_message(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert(
            "end",
            "Sistema listo.\n"
            "Ingresa los parámetros en el panel superior y presiona 'Calcular Mejores Combinaciones'.\n",
        )
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
            self.textbox.insert("end", "Buscando combinaciones para:\n")
            self.textbox.insert(
                "end",
                f"f = {f} Hz | H = {H} V | Vcc = {Vcc} V | Tolerancia ≤ {tol * 100:.1f}%\n",
            )
            self.textbox.insert("end", f"Serie: {serie}\n\n")
            self.textbox.insert("end", "Calculando... (puede tardar unos segundos)\n\n")
            self.update()

            resultados = seleccionar_componentes(f, H, Vcc, tol=tol, serie=serie, top_n=20)

            self.textbox.delete("1.0", "end")
            if not resultados:
                self.textbox.insert("end", "No se encontraron combinaciones dentro de la tolerancia.\n")
                self.textbox.insert("end", "Intenta aumentar la tolerancia o cambiar los valores.")
            else:
                self.textbox.insert("end", f"Se encontraron {len(resultados)} combinaciones válidas:\n\n")
                self.textbox.insert(
                    "end",
                    f"{'R1 (Ω)':>10} {'R2 (Ω)':>10} {'Ra (Ω)':>10} {'Cf (nF)':>10} {'H_calc (V)':>12} {'f_calc (Hz)':>13} {'Error (%)':>10}\n",
                )
                self.textbox.insert("end", "-" * 92 + "\n")

                for r in resultados:
                    linea = (
                        f"{r['R1']:>10.1f} {r['R2']:>10.1f} {r['Ra']:>10.1f} {r['Cf']:>10.2f} "
                        f"{r['H_calc']:>12.3f} {r['f_calc']:>13.2f} {r['error_%']:>10.2f}\n"
                    )
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
