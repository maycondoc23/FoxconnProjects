import trimesh

def read_3d_file(file_path):
    # Carregar a malha 3D
    mesh = trimesh.load(file_path)

    # Exibir informações sobre a malha
    print(f"Vértices: {len(mesh.vertices)}")
    print(f"Faces: {len(mesh.faces)}")
    
    # Exibir as coordenadas dos vértices
    print("Vértices:")
    for vertex in mesh.vertices:
        print(f"- {vertex}")

# Caminho para o arquivo 3D
file_path = r"C:\MAYCON\LOGS0904\WARP\ML07_20250407062841\R21_3_1_0407062841.3d"
read_3d_file(file_path)
