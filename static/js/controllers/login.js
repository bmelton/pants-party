angular.module('PantsParty')
    .controller('TokenCtrl', function($scope, $auth, $state, $http) {
        if($state.params.token) {
            $http.get("/api/verify-token/" + $state.params.token)
                .success(function(data) {
                    console.log(data);
                    $scope.verified = true;
                    swal("Verified", "Your token has been verified, and you are a full-fledged member of society, or like, an astronaut, or something.", "success");
                })
                .error(function(data) {
                    $scope.verified = false;
                    swal("Not verified", "For some odd reason, your token was not verified.  I can't imagine why this would be, so that really sucks.", "error");
                })
        }
    })

    .controller('LoginCtrl', function($scope, $auth) {
        $scope.login = function() {
            $auth.login({ username: $scope.username, password: $scope.password })
                .then(function() {
                    console.log("Successful login");
                })
                .catch(function(response) {
                    console.log(response.data.message);
                });
        }

        $scope.authenticate = function(provider) {
            $auth.authenticate(provider)
                .then(function() {
                    $scope.$broadcast("loginout", "on!");
                })
                .catch(function(response) {
                    console.log(response.data ? response.data.message : response);
                });
        };
    })

    .controller('HelloCtrl', ['$scope', '$state', '$http', '$rootScope', function($scope, $state, $http, $rootScope) {
        $scope.uploadSuccess = function(response) { 
            $scope.userData.avatar = null;
            console.log(response.data.data);
            $scope.userData.avatar = response.data.data;
            $rootScope.$broadcast("avatarChanged");
            swal("Hooray!", "You saved your avatar.  That's cool, I guess.", "success");
        };

        $scope.uploadError = function(response) { 
            console.log(response);
            swal("Ouch!", "So, the thing you tried to do? It didn't work.", "error");
        };

        $http.get("/api/users/me/")
            .success(function(data) {
                $scope.userData = data;
                console.log($scope.userData.avatar);
                if($scope.userData.avatar !== "")
                    localStorage.setItem("avatar", data.avatar);
                else
                    localStorage.setItem("avatar", "/static/images/anonymous.png");
                localStorage.setItem("username", data.display_name);
                $rootScope.$broadcast("avatarChanged");
            })

        $scope.helloForm = function(form) { 
            $http.post("/api/users/me/", $scope.userData)
                .success(function(data) {
                    $scope.userData = data;
                    swal("Hooray!", "You saved your thing.  That's cool.", "success");
                    console.log(data);
                })
                .error(function(data) {
                    console.log(data);
                    alert("Hi!");
                })
            console.log($scope.userData);
        };

        $scope.available = true;
        $scope.usernameAvailable = function() { 
            if(typeof($scope.userData.username) === "undefined") {
                $scope.available = false;
            } else { 
                if($scope.userData.username.length <= 2)
                    $scope.available = false;
                else { 
                    $http.get("/api/username/available/" + $scope.userData.username)
                        .success(function(data) {
                            $scope.available = data.available;
                        })
                }
            };
        };

        var unmet_condition = false;
        if(unmet_condition) 
            $state.go("home");
    }])

    .controller('ProfileCtrl', function($scope, $auth, $http, $stateParams) {
        if($stateParams.profileId) {
            console.log($stateParams.profileId);
            $scope.isAuthenticated = function() {
                return $auth.isAuthenticated();
            }


            $http.get("/api/users/" + $stateParams.profileId)
                .success(function(data) { 
                    $scope.profile = data;
                })
                .error(function(data) { 
                    swal("404", "This user does not exist.", "error");
                })
        } else { 
            swal("404", "This user does not exist.", "error");
        }
    })
