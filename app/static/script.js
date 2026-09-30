// Inicializar o mapa na metade esquerda da tela
const map = L.map('map').setView([20, 0], 2); // Centro no mapa mundial

// Adicionar camada de visualização (OpenStreetMap)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Exemplo: Mostrar um marcador em Portugal
const portugal = L.polygon([
    [41.1475, -8.611],  // Porto
    [38.7223, -9.139],  // Lisboa
    [37.0179, -7.930]   // Algarve
]).addTo(map);

// Evento de clique no polígono de Portugal
portugal.on('click', function() {
    console.log("Clicou em Portugal!");
    fetchContratos({ pais: 'Portugal' });
});

// Função para buscar contratos do backend
function fetchContratos(filtros) {
    let url = '/api/contratos?';
    if (filtros.pais) url += `pais=${filtros.pais}&`;
    
    // Requisição ao backend
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const lista = document.getElementById('lista-contratos');
            lista.innerHTML = '';  // Limpa a lista antes de adicionar os novos contratos
            data.forEach(contrato => {
                const li = document.createElement('li');
                li.textContent = contrato[1];  // Exemplo: nome do contrato
                lista.appendChild(li);
            });
        })
        .catch(error => console.error("Erro ao buscar contratos:", error));
}

