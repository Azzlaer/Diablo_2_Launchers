Imports System.IO
Imports Microsoft.Win32

Public Class Form1

    Dim gameExePath As String

    Private Sub Form1_FormClosed(sender As Object, e As System.Windows.Forms.FormClosedEventArgs) Handles Me.FormClosed
    End Sub ' Variable global para almacenar la ruta del archivo "Game.exe"

    Private Sub Form1_Load(sender As Object, e As EventArgs) Handles MyBase.Load
        'Auto completar el textbox con la ruta del archivo "Game.exe"
        gameExePath = Path.Combine(Application.StartupPath, "Game.exe")
        If File.Exists(gameExePath) Then
            txtparametros.Text = gameExePath
            txtparametros.BackColor = Color.Green
        Else
            txtparametros.Text = "Archivo no encontrado"
            MsgBox("Ejecuta el Launcher en la carpeta de Diablo II", vbInformation)
            Me.Close()
        End If
    End Sub

    Private Sub rdNormal_CheckedChanged(sender As Object, e As EventArgs) Handles rdNormal.CheckedChanged
        If rdVentana.Checked = True Then
            chk3dfx.Checked = True
            chk3dfx.Enabled = False
        End If

        UpdateParameters()
        ' AddToLog("Se habilitó la opción Normal")
    End Sub

    Private Sub rdVentana_CheckedChanged(sender As Object, e As EventArgs) Handles rdVentana.CheckedChanged
        UpdateParameters()
        'AddToLog("Se habilitó la opción Ventana")
        ' Deshabilitamos y desmarcamos chk3dfx si rdVentana está seleccionado
        If rdVentana.Checked Then
            chk3dfx.Enabled = False
            chk3dfx.Checked = False
            If lstParametros.Items.Contains("-w") Then
                lstParametros.Items.Remove("-w")
            End If
        Else
            chk3dfx.Enabled = True
        End If

        UpdateParameters()
        'AddToLog("Se habilitó la opción Ventana")
    End Sub

    Private Sub chk3dfx_CheckedChanged(sender As Object, e As EventArgs) Handles chk3dfx.CheckedChanged
        UpdateParameters()
    End Sub

    Private Sub chkskip_CheckedChanged(sender As Object, e As EventArgs) Handles chkskip.CheckedChanged
        UpdateParameters()
    End Sub

    Private Sub chksound_CheckedChanged(sender As Object, e As EventArgs) Handles chksound.CheckedChanged
        UpdateParameters()
    End Sub

    Private Sub chkfocus_CheckedChanged(sender As Object, e As EventArgs) Handles chkfocus.CheckedChanged
        UpdateParameters()
    End Sub

    Private Sub btnJugar_Click(sender As Object, e As EventArgs) Handles btnJugar.Click


        ' Obtenemos los parámetros del ListBox
        Dim parameters As String = txtparametros.Text & " " & String.Join(" ", lstParametros.Items.Cast(Of String)())

        ' Mostramos los parámetros en un MessageBox (aquí deberías ejecutar el archivo con los parámetros)
        'MessageBox.Show("Ejecutando: " & parameters)

        ' Aquí deberías ejecutar el archivo Game.exe con los parámetros
        Try
            Process.Start(txtparametros.Text, String.Join(" ", lstParametros.Items.Cast(Of String)()))
        Catch ex As Exception
            MessageBox.Show("Error al ejecutar el archivo: " & ex.Message)
        End Try

    End Sub

    Private Sub UpdateParameters()
        ' Limpiamos el contenido del ListBox
        lstParametros.Items.Clear()

        ' Verificamos el estado de los RadioButtons y CheckBoxes y agregamos los parámetros correspondientes al ListBox
        If rdVentana.Checked Then
            lstParametros.Items.Add("-w")
        End If

        If chk3dfx.Checked Then
            lstParametros.Items.Add("-3dfx")
        End If

        If chkskip.Checked Then
            lstParametros.Items.Add("-skiptobnet")
        End If

        If chksound.Checked Then
            lstParametros.Items.Add("-ns")
        End If

        If chkfocus.Checked Then
            lstParametros.Items.Add("-nohide")
        End If
    End Sub

    Private Sub AddToLog(entry As String)
        Dim logEntry As String = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") & " - " & entry
        ListBox1.Items.Add(logEntry)
    End Sub

    Private Sub Button2_Click(sender As System.Object, e As System.EventArgs) Handles Button2.Click
        Try
            ' Ruta de la clave de registro HKEY_CURRENT_USER\Software\Battle.net\Configuration
            Dim battleNetKey As RegistryKey = Registry.CurrentUser.CreateSubKey("Software\Battle.net\Configuration")

            ' Establecer el valor "Diablo II Battle.net Gateways" en la clave de registro
            battleNetKey.SetValue("Diablo II Battle.net Gateways", New Byte() {&H31, &H30, &H30, &H32, &H0, &H30, &H31, &H0, &H34, &H35, &H2E, &H32, &H33, &H31, &H2E, &H32, &H31, &H35, &H2E, &H31, &H34, &H31, &HA, &H0, &H2D, &H34, &H0, &H44, &H32, &H52, &H65, &H76, &H65, &H6E, &H67, &H65, &H0, &H0}, RegistryValueKind.Binary)

            ' Ruta de la clave de registro HKEY_CURRENT_USER\Software\Blizzard Entertainment\Diablo II
            Dim diabloIIKey As RegistryKey = Registry.CurrentUser.CreateSubKey("Software\Blizzard Entertainment\Diablo II")

            ' Establecer los valores "CmdLine" y "BNETIP" en la clave de registro
            diabloIIKey.SetValue("CmdLine", "-skiptobnet")
            diabloIIKey.SetValue("BNETIP", "45.231.215.141")

            ' Cerrar las claves de registro
            battleNetKey.Close()
            diabloIIKey.Close()

            MessageBox.Show("Configuración de registro aplicada correctamente.")
        Catch ex As Exception
            MessageBox.Show("Error al aplicar la configuración de registro: " & ex.Message)
        End Try
    End Sub

    Private Sub Button1_Click(sender As System.Object, e As System.EventArgs) Handles Button1.Click
        Try
            ' Abrimos la clave del registro
            Using key As RegistryKey = Registry.CurrentUser.CreateSubKey("Software\Blizzard Entertainment\Diablo II")

                ' Escribimos los valores en el registro
                key.SetValue("Contrast", &H32, RegistryValueKind.DWord)
                key.SetValue("Gamma", &H9B, RegistryValueKind.DWord)

                MessageBox.Show("Registro modificado correctamente.", "Éxito", MessageBoxButtons.OK, MessageBoxIcon.Information)
            End Using
        Catch ex As Exception
            MessageBox.Show("Error al modificar el registro: " & ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
        End Try
    End Sub

    Private Sub Button3_Click(sender As System.Object, e As System.EventArgs) Handles Button3.Click
        Try
            ' Abre la clave del registro
            Dim key As RegistryKey = Registry.CurrentUser.OpenSubKey("Software\Blizzard Entertainment", True)

            If key IsNot Nothing Then
                ' Elimina la subclave Diablo II
                key.DeleteSubKeyTree("Diablo II")
                MessageBox.Show("Clave eliminada correctamente.")
            Else
                MessageBox.Show("Clave no encontrada.")
            End If

        Catch ex As Exception
            MessageBox.Show("Error al eliminar la clave: " & ex.Message)
        End Try

    End Sub
End Class
