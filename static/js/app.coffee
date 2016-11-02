angular.module 'app', []

.controller 'rootController', ['$scope','$http', ($scope, $http)->
  $scope.getPanelClass = (site)->
    status = site.status_code
    if status == 200
      return 'panel-default'
    if status >= 500
      return 'panel-error'
    return 'panel-warning'

  formatResponseError = (response)->
    if !!response.data and !!response.data.error
      return response.data.error
    else if response.status == -1
      return "Connection failed"
    else
      return '[' + response.status + '] ' + response.statusText

  $scope.load_servers = ->
    $scope.loading = true
    $scope.servers = []
    $scope.last_scan = undefined
    $http.get('/api/servers').then (response)->
      $scope.loading = false
      data = response.data
      $scope.servers = data.servers
      if data.last_scan
        $scope.last_scan = moment.utc(data.last_scan).fromNow()
    , (response)->
      $scope.loading = false
      alert(formatResponseError(response))

  $scope.rescan = ->
    $scope.scanning = true
    $http.get('/api/scan').then (response)->
      $scope.scanning = false
      $scope.load_servers()
    , (response)->
      $scope.scanning = false
      alert(formatResponseError(response))

  $scope.load_servers()
]