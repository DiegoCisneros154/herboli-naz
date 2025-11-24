from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector

app = Flask(__name__)
app.secret_key = 'clave_super_secreta'



# --- BORRA LO QUE TENÍAS DE URLPARSE Y O.ENVIRON ---
# --- PEGA ESTO EXACTAMENTE: ---

DB_CONFIG = {
    "host": "trolley.proxy.rlwy.net",       # El mismo host de Workbench
    "user": "root",                         # El mismo usuario
    "password": "cdBeiqOovDCuwMseZEvxdXrMAJeKzeGA", # Tu contraseña REAL
    "database": "railway",                  # 👈 IMPORTANTE: Forzamos la base 'railway'
    "port": 39658                           # El puerto correcto
}

def obtener_conexion():
    # Esta función ya usará la configuración forzada de arriba
    return mysql.connector.connect(**DB_CONFIG)


# Página principal
@app.route('/')
def index():
    return render_template('index.html')



# Registro de usuarios
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        correo = request.form['correo']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        rol = 'usuario'

        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        # 🔍 Validar si existe usuario
        cursor.execute("SELECT * FROM usuarios WHERE usuario=%s", (usuario,))
        existe_usuario = cursor.fetchone()

        if existe_usuario:
            return render_template("register.html",
                                   error="❌ El nombre de usuario ya está en uso.")

        # 🔍 Validar si existe correo
        cursor.execute("SELECT * FROM usuarios WHERE correo=%s", (correo,))
        existe_correo = cursor.fetchone()

        if existe_correo:
            return render_template("register.html",
                                   error="❌ El correo ya está registrado.")

        # ✔ Insertar en usuarios
        cursor.execute("""
            INSERT INTO usuarios (usuario, password, correo, telefono, direccion, rol)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (usuario, password, correo, telefono, direccion, rol))
        conexion.commit()

        # ✔ Obtener el id del nuevo usuario
        cursor.execute("SELECT LAST_INSERT_ID()")
        id_usuario = cursor.fetchone()['LAST_INSERT_ID()']

        # ✔ Insertar en clientes
        cursor.execute("""
            INSERT INTO clientes (id, nombre, direccion, telefono)
            VALUES (%s, %s, %s, %s)
        """, (id_usuario, usuario, direccion, telefono))
        conexion.commit()

        cursor.close()
        conexion.close()

        return redirect(url_for('login'))

    return render_template('register.html')



# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute('SELECT * FROM usuarios WHERE usuario=%s AND password=%s', (usuario, password))
        user = cursor.fetchone()
        cursor.close()
        conexion.close()
        if user:
            session['usuario'] = user['usuario']
            session['rol'] = user['rol']
            # Redirige según el rol
            if user['rol'] == 'admin':
                return redirect(url_for('index'))
            else:
                return redirect(url_for('index'))  # 👈 Redirige al inicio con sesión activa
        else:
            return render_template('login.html', error='Usuario o contraseña incorrectos')
    return render_template('login.html')


# Panel cliente
@app.route('/cliente')
def cliente_dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute('SELECT * FROM usuarios WHERE usuario = %s', (session['usuario'],))
    cliente = cursor.fetchone()
    cursor.close()
    conexion.close()
    return render_template('cliente_dashboard.html', cliente=cliente)

# Panel administrador
@app.route('/admin')
def admin_dashboard():
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect(url_for('login'))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute('SELECT * FROM clientes')
    clientes = cursor.fetchall()

    cursor.execute('SELECT * FROM plantas')
    plantas = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template('admin_dashboard.html', usuario=session['usuario'], clientes=clientes, plantas=plantas)


# CRUD clientes
@app.route('/cliente/buscar', methods=['POST'])
def buscar_cliente():
    id_cliente = request.json.get('idCliente')
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute('SELECT * FROM clientes WHERE id = %s', (id_cliente,))
    cliente = cursor.fetchone()
    cursor.close()
    conexion.close()
    return jsonify(cliente if cliente else {})

@app.route('/cliente/guardar', methods=['POST'])
def guardar_cliente():
    data = request.json
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute('INSERT INTO clientes (id, nombre, direccion, telefono) VALUES (%s, %s, %s, %s)',
                       (data['idCliente'], data['nombre'], data['direccion'], data['telefono']))
        conexion.commit()
        mensaje = 'Cliente guardado correctamente'
    except mysql.connector.IntegrityError:
        mensaje = 'Error: El ID ya existe o los datos son inválidos'
    cursor.close()
    conexion.close()
    return jsonify({'mensaje': mensaje})


@app.route('/cliente/modificar', methods=['POST'])
def modificar_cliente():
    data = request.json
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute('UPDATE clientes SET nombre = %s, direccion = %s, telefono = %s WHERE id = %s',
                   (data['nombre'], data['direccion'], data['telefono'], data['idCliente']))
    conexion.commit()
    cursor.close()
    conexion.close()
    return jsonify({'mensaje': 'Cliente modificado correctamente'})

@app.route('/cliente/eliminar', methods=['POST'])
def eliminar_cliente():
    id_cliente = request.json.get('idCliente')
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute('DELETE FROM clientes WHERE id = %s', (id_cliente,))
    conexion.commit()
    cursor.close()
    conexion.close()
    return jsonify({'mensaje': 'Cliente eliminado correctamente'})


# Catálogo de plantas
@app.route('/plantas')
def plantas():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute('SELECT * FROM plantas')
    lista_plantas = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template('plantas.html', plantas=lista_plantas)

# Página de empresa
@app.route('/empresa')
def empresa():
    return render_template('empresa.html')

# Testimonios
@app.route('/testimonios', methods=['GET', 'POST'])
def testimonios():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute('SELECT * FROM usuarios WHERE usuario = %s', (session['usuario'],))
    cliente = cursor.fetchone()
    if request.method == 'POST':
        mensaje = request.form['mensaje']
        cursor.execute('INSERT INTO testimonios (cliente_id, nombre, telefono, mensaje) VALUES (%s, %s, %s, %s)',
                       (cliente['id'], cliente['usuario'], cliente['telefono'], mensaje))
        conexion.commit()
    cursor.execute('SELECT * FROM testimonios ORDER BY id DESC')
    lista_testimonios = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template('testimonios.html', cliente=cliente, testimonios=lista_testimonios)

# Edición de perfil
@app.route('/editar_perfil', methods=['GET', 'POST'])
def editar_perfil():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute('SELECT * FROM usuarios WHERE usuario = %s', (session['usuario'],))
    cliente = cursor.fetchone()
    if request.method == 'POST':
        nuevo_usuario = request.form['usuario']
        correo = request.form['correo']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        cursor.execute('UPDATE usuarios SET usuario = %s, correo = %s, telefono = %s, direccion = %s WHERE id = %s',
                       (nuevo_usuario, correo, telefono, direccion, cliente['id']))
        conexion.commit()
        session['usuario'] = nuevo_usuario
        cursor.close()
        conexion.close()
        return redirect(url_for('cliente_dashboard'))
    cursor.close()
    conexion.close()
    return render_template('editar_perfil.html', cliente=cliente)

# Cierre de sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/carrito/agregar', methods=['POST'])
def agregar_al_carrito():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    planta_id = request.form['planta_id']
    cantidad = int(request.form['cantidad'])

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute('SELECT id FROM usuarios WHERE usuario = %s', (session['usuario'],))
    usuario = cursor.fetchone()
    cliente_id = usuario['id']

    # Verifica si ya existe el producto en el carrito
    cursor.execute('SELECT * FROM carrito WHERE cliente_id = %s AND planta_id = %s', (cliente_id, planta_id))
    existente = cursor.fetchone()

    if existente:
        cursor.execute('UPDATE carrito SET cantidad = cantidad + %s WHERE cliente_id = %s AND planta_id = %s',
                       (cantidad, cliente_id, planta_id))
    else:
        cursor.execute('INSERT INTO carrito (cliente_id, planta_id, cantidad) VALUES (%s, %s, %s)',
                       (cliente_id, planta_id, cantidad))

    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('plantas'))


@app.route('/carrito')
def ver_carrito():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute('SELECT id FROM usuarios WHERE usuario = %s', (session['usuario'],))
    usuario = cursor.fetchone()
    cliente_id = usuario['id']

    cursor.execute('''
        SELECT c.id, p.nombre, p.precio, c.cantidad, (p.precio * c.cantidad) AS total
        FROM carrito c
        JOIN plantas p ON c.planta_id = p.id
        WHERE c.cliente_id = %s
    ''', (cliente_id,))
    productos = cursor.fetchall()

    cursor.close()
    conexion.close()
    return render_template('carrito.html', productos=productos)

@app.route('/carrito/eliminar/<int:id>', methods=['POST'])
def eliminar_del_carrito(id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute('DELETE FROM carrito WHERE id = %s', (id,))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('ver_carrito'))


@app.route('/admin/plantas', methods=['POST'])
def administrar_plantas():
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect(url_for('login'))

    planta_id = request.form['id']
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    precio = request.form['precio']
    imagen = request.form['imagen']

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute('''
        UPDATE plantas
        SET nombre = %s, descripcion = %s, precio = %s, imagen = %s
        WHERE id = %s
    ''', (nombre, descripcion, precio, imagen, planta_id))
    conexion.commit()
    cursor.close()
    conexion.close()

    return redirect(url_for('configuracion'))

@app.route('/admin/plantas/agregar', methods=['POST'])
def agregar_planta():
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect(url_for('login'))

    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    precio = request.form['precio']
    imagen = request.form['imagen']

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute('''
        INSERT INTO plantas (nombre, descripcion, precio, imagen)
        VALUES (%s, %s, %s, %s)
    ''', (nombre, descripcion, precio, imagen))
    conexion.commit()
    cursor.close()
    conexion.close()

    return redirect(url_for('configuracion'))


@app.route('/carrito/actualizar/<int:id>', methods=['POST'])
def actualizar_cantidad(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    nueva_cantidad = int(request.form['cantidad'])

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # Actualiza la cantidad en el carrito
    cursor.execute('UPDATE carrito SET cantidad = %s WHERE id = %s', (nueva_cantidad, id))
    conexion.commit()

    cursor.close()
    conexion.close()
    return redirect(url_for('ver_carrito'))

# --- CHECKOUT: Resumen de compra ---
@app.route('/checkout', methods=['GET'])
def checkout():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # ✅ Incluye direccion en la consulta
    cursor.execute('SELECT id, usuario, correo, direccion FROM usuarios WHERE usuario = %s', (session['usuario'],))
    usuario = cursor.fetchone()
    cliente_id = usuario['id']

    # Obtener productos del carrito
    cursor.execute('''
        SELECT c.planta_id, p.nombre, p.precio AS precio, c.cantidad
        FROM carrito c
        JOIN plantas p ON c.planta_id = p.id
        WHERE c.cliente_id = %s
    ''', (cliente_id,))
    carrito = cursor.fetchall()

    if not carrito:
        cursor.close()
        conexion.close()
        return redirect(url_for('plantas'))

    total_pedido = 0
    for item in carrito:
        item['total'] = item['precio'] * item['cantidad']
        total_pedido += item['total']

    cursor.close()
    conexion.close()

    # Renderizar la plantilla con los datos del usuario (incluyendo dirección)
    return render_template('checkout.html', productos=carrito, total=total_pedido, usuario=usuario)


@app.route('/compras')
def compras_realizadas():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # Obtener ID del usuario
    cursor.execute('SELECT id FROM usuarios WHERE usuario = %s', (session['usuario'],))
    usuario = cursor.fetchone()
    cliente_id = usuario['id']

    # Obtener todos los pedidos del usuario
    cursor.execute('SELECT id, total, fecha FROM pedidos WHERE cliente_id = %s ORDER BY fecha DESC', (cliente_id,))
    pedidos = cursor.fetchall()

    compras = []

    for pedido in pedidos:
        # Obtener productos asociados a cada pedido
        cursor.execute('''
            SELECT p.nombre, c.cantidad, c.precio_unitario AS precio, (c.precio_unitario * c.cantidad) AS total
            FROM detalle_pedidos c
            JOIN plantas p ON c.planta_id = p.id
            WHERE c.pedido_id = %s
        ''', (pedido['id'],))
        productos = cursor.fetchall()

        compras.append({
            'pedido': pedido,
            'productos': productos,
            'total': pedido['total']  # ✅ Usamos el total guardado en la tabla pedidos
        })

    cursor.close()
    conexion.close()

    return render_template('compras.html', compras=compras)



@app.route('/admin/index')
def admin_index():
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_index.html', usuario=session['usuario'])

@app.route('/admin/compras')
def admin_compras():
    # Verificar que el usuario esté logueado y sea admin
    if 'usuario' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # Consulta para obtener todas las compras con información del cliente
    cursor.execute('''
        SELECT 
            p.id AS pedido_id,
            p.cliente_id,
            u.usuario AS cliente_nombre,
            u.telefono AS cliente_telefono,
            dp.planta_id,
            pl.nombre AS tipo_arbol,
            dp.cantidad,
            dp.precio_unitario AS precio,
            (dp.cantidad * dp.precio_unitario) AS total,
            p.fecha
        FROM pedidos p
        JOIN usuarios u ON p.cliente_id = u.id
        JOIN detalle_pedidos dp ON dp.pedido_id = p.id
        JOIN plantas pl ON dp.planta_id = pl.id
        ORDER BY p.cliente_id, p.fecha DESC
    ''')

    compras = cursor.fetchall()

    # 🔹 Aseguramos que la fecha siempre esté formateada correctamente
    for compra in compras:
        if compra['fecha']:
            # Si es cadena, no tiene strftime → convertimos manualmente
            if isinstance(compra['fecha'], str):
                compra['fecha'] = compra['fecha'][:10]  # solo la parte de yyyy-mm-dd
            else:
                compra['fecha'] = compra['fecha'].strftime('%d/%m/%Y')

    cursor.close()
    conexion.close()

    # Renderizamos el template
    return render_template('admin_compras.html', compras=compras)



@app.route('/configuracion')
def configuracion():
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect(url_for('login'))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # Traer todas las plantas
    cursor.execute("SELECT * FROM plantas")
    plantas = cursor.fetchall()

    # Traer todos los clientes
    cursor.execute("SELECT id, nombre, direccion, telefono FROM clientes")
    clientes = cursor.fetchall()

    cursor.close()
    conexion.close()

    # Pasar usuario, plantas y clientes al HTML
    return render_template(
        'configuracion.html', 
        usuario=session['usuario'], 
        plantas=plantas,
        clientes=clientes
    )

# --- CRUD de Proveedores ---
@app.route('/proveedores')
def proveedores():
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect(url_for('login'))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute('SELECT * FROM proveedores ORDER BY nombre ASC')
    proveedores = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template('proveedores.html', proveedores=proveedores)


@app.route('/agregar_proveedor', methods=['POST'])
def agregar_proveedor():
    nombre = request.form['nombre']
    telefono = request.form['telefono']
    correo = request.form['correo']
    producto = request.form['producto']
    direccion = request.form['direccion']
    calificacion = request.form.get('calificacion', 5)
    notas = request.form.get('notas', '')

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute('''
        INSERT INTO proveedores (nombre, telefono, correo, producto, direccion, calificacion, notas)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    ''', (nombre, telefono, correo, producto, direccion, calificacion, notas))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('proveedores'))


@app.route('/editar_proveedor/<int:id>', methods=['POST'])
def editar_proveedor(id):
    nombre = request.form['nombre']
    telefono = request.form['telefono']
    correo = request.form['correo']
    producto = request.form['producto']
    direccion = request.form['direccion']
    calificacion = request.form.get('calificacion', 5)
    notas = request.form.get('notas', '')

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute('''
        UPDATE proveedores 
        SET nombre=%s, telefono=%s, correo=%s, producto=%s, direccion=%s, calificacion=%s, notas=%s 
        WHERE id=%s
    ''', (nombre, telefono, correo, producto, direccion, calificacion, notas, id))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('proveedores'))


@app.route('/eliminar_proveedor/<int:id>')
def eliminar_proveedor(id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute('DELETE FROM proveedores WHERE id=%s', (id,))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('proveedores'))

@app.route('/procesar_checkout', methods=['POST'])
def procesar_checkout():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute('SELECT id FROM usuarios WHERE usuario = %s', (session['usuario'],))
    usuario = cursor.fetchone()
    cliente_id = usuario['id']

    cursor.execute('''
        SELECT c.planta_id, p.nombre, p.precio AS precio, c.cantidad
        FROM carrito c
        JOIN plantas p ON c.planta_id = p.id
        WHERE c.cliente_id = %s
    ''', (cliente_id,))
    carrito = cursor.fetchall()

    if not carrito:
        cursor.close()
        conexion.close()
        return redirect(url_for('plantas'))

    total_pedido = 0
    for item in carrito:
        item['total'] = item['precio'] * item['cantidad']
        total_pedido += item['total']

    try:
        cursor.execute(
            'INSERT INTO pedidos (cliente_id, fecha, total) VALUES (%s, NOW(), %s)',
            (cliente_id, total_pedido)
        )
        pedido_id = cursor.lastrowid

        for item in carrito:
            cursor.execute('''
                INSERT INTO detalle_pedidos (pedido_id, planta_id, cantidad, precio_unitario)
                VALUES (%s, %s, %s, %s)
            ''', (pedido_id, item['planta_id'], item['cantidad'], item['precio']))

        cursor.execute('DELETE FROM carrito WHERE cliente_id = %s', (cliente_id,))
        conexion.commit()

    except Exception as e:
        conexion.rollback()
        print("Error en checkout:", e)
        cursor.close()
        conexion.close()
        return "Ocurrió un error durante el proceso de compra."

    cursor.close()
    conexion.close()

    return render_template('confirmacion.html', pedido={'id': pedido_id}, productos=carrito, total=total_pedido)

@app.route('/planta/eliminar', methods=['POST'])
def eliminar_planta():
    data = request.get_json()
    planta_id = data.get('id')

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute('DELETE FROM plantas WHERE id = %s', (planta_id,))
    conexion.commit()

    cursor.close()
    conexion.close()

    return jsonify({'mensaje': 'Planta eliminada correctamente'})


# Ejecutar servidor
if __name__ == '__main__':
    app.run(debug=True)
