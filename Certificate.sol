// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CertificateRegistry {
    struct Certificate {
        bytes32 hash;
        address issuer;
        uint256 issuedAt;
        bool revoked;
    }

    mapping(string => Certificate) private certificates;
    address public owner;

    event CertificateStored(string certId, bytes32 hash, address indexed issuer, uint256 timestamp);
    event CertificateRevoked(string certId, address indexed issuer, uint256 timestamp);
    event OwnerTransferred(address indexed previousOwner, address indexed newOwner);

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _; // required placeholder
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "zero address");
        emit OwnerTransferred(owner, newOwner);
        owner = newOwner;
    }

    function storeCertificate(string memory certId, bytes32 hash) external onlyOwner {
        certificates[certId] = Certificate({
            hash: hash,
            issuer: msg.sender,
            issuedAt: block.timestamp,
            revoked: false
        });
        emit CertificateStored(certId, hash, msg.sender, block.timestamp);
    }

    function revokeCertificate(string memory certId) external onlyOwner {
        certificates[certId].revoked = true;
        emit CertificateRevoked(certId, msg.sender, block.timestamp);
    }

    function getCertificateHash(string memory certId) external view returns (bytes32) {
        return certificates[certId].hash;
    }

    function isRevoked(string memory certId) external view returns (bool) {
        return certificates[certId].revoked;
    }

    function exists(string memory certId) external view returns (bool) {
        return certificates[certId].issuedAt != 0 || certificates[certId].issuer != address(0);
    }
}