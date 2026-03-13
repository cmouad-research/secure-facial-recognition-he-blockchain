// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ControlPlane {
    enum Status { NONE, ACTIVE, REVOKED }

    struct UserRec {
        Status status;
        bytes32 cidHash;
        uint64 keyVersion;
        uint64 createdAt;
        uint64 updatedAt;
    }

    address public admin;
    mapping(address => bool) public verifiers;
    mapping(bytes32 => UserRec) public users;

    event UserEnrolled(bytes32 indexed userId, bytes32 cidHash, uint64 keyVersion);
    event UserRevoked(bytes32 indexed userId);
    event VerifierSet(address indexed verifier, bool allowed);
    event AuthRequested(bytes32 indexed reqId, bytes32 indexed userId, address indexed verifier, bytes32 scoreCtHash);
    event AuthDecided(bytes32 indexed reqId, bool accepted, bytes32 scorePtHash, uint64 decidedAt);

    modifier onlyAdmin() { require(msg.sender == admin, "admin"); _; }
    modifier onlyVerifier() { require(verifiers[msg.sender], "verifier"); _; }

    constructor() { admin = msg.sender; }

    function setVerifier(address v, bool allowed) external onlyAdmin {
        verifiers[v] = allowed;
        emit VerifierSet(v, allowed);
    }

    function enroll(bytes32 userId, bytes32 cidHash, uint64 keyVersion) external onlyAdmin {
        users[userId] = UserRec(Status.ACTIVE, cidHash, keyVersion, uint64(block.timestamp), uint64(block.timestamp));
        emit UserEnrolled(userId, cidHash, keyVersion);
    }

    function revoke(bytes32 userId) external onlyAdmin {
        require(users[userId].status == Status.ACTIVE, "not active");
        users[userId].status = Status.REVOKED;
        users[userId].updatedAt = uint64(block.timestamp);
        emit UserRevoked(userId);
    }

    function requestAuth(bytes32 reqId, bytes32 userId, bytes32 scoreCtHash) external onlyVerifier {
        require(users[userId].status == Status.ACTIVE, "not active");
        emit AuthRequested(reqId, userId, msg.sender, scoreCtHash);
    }

    function decide(bytes32 reqId, bool accepted, bytes32 scorePtHash) external onlyAdmin {
        emit AuthDecided(reqId, accepted, scorePtHash, uint64(block.timestamp));
    }

    function getUser(bytes32 userId) external view returns (UserRec memory) {
        return users[userId];
    }
}
